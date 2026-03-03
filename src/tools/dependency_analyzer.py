"""Dependency Analyzer Module - Maven/Gradle support (multi-module aware)"""
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


def _extract_gradle_deps_block(content: str) -> Optional[str]:
    """Extract Gradle dependencies block content using brace counting."""
    match = re.search(r'dependencies\s*\{', content)
    if not match:
        return None
    start = match.end()
    depth = 1
    pos = start
    while pos < len(content) and depth > 0:
        if content[pos] == '{':
            depth += 1
        elif content[pos] == '}':
            depth -= 1
        pos += 1
    if depth == 0:
        return content[start:pos - 1]
    return None


def _find_all_build_files(project_path: str, filename_patterns: List[str]) -> List[str]:
    """Walk project tree and return all files matching any of the given names."""
    found = []
    for root, dirs, files in os.walk(project_path):
        # Skip generated/hidden directories
        dirs[:] = [d for d in dirs if d not in ('target', 'build', '.git', 'node_modules', '.gradle')]
        for name in files:
            if name in filename_patterns:
                found.append(os.path.join(root, name))
    return found


def _module_name_from_path(file_path: str, project_path: str) -> str:
    """Derive a human-readable module name from the build file path."""
    rel = os.path.relpath(os.path.dirname(file_path), project_path)
    return rel if rel != '.' else '(root)'


async def analyze_dependencies(project_path: str, build_tool: str = 'auto') -> Dict:
    """Analyze Maven or Gradle dependencies (multi-module aware)."""
    if build_tool == 'auto':
        has_pom = bool(_find_all_build_files(project_path, ['pom.xml']))
        has_gradle = bool(_find_all_build_files(project_path, ['build.gradle', 'build.gradle.kts']))
        if has_pom:
            build_tool = 'maven'
        elif has_gradle:
            build_tool = 'gradle'
        else:
            return {'error': 'No Maven (pom.xml) or Gradle (build.gradle) found'}
    if build_tool == 'maven':
        return await analyze_maven(project_path)
    elif build_tool == 'gradle':
        return await analyze_gradle(project_path)
    return {'error': f'Unknown build tool: {build_tool}'}


# ---------------------------------------------------------------------------
# Maven
# ---------------------------------------------------------------------------
def _parse_pom(pom_path: str) -> Tuple[List[Dict], List[Dict]]:
    """Parse a single pom.xml and return (dependencies, issues)."""
    deps: List[Dict] = []
    issues: List[Dict] = []
    try:
        tree = ET.parse(pom_path)
        root = tree.getroot()
        ns = {'m': 'http://maven.apache.org/POM/4.0.0'}
        dep_nodes = root.findall('.//m:dependency', ns)
        if not dep_nodes:
            dep_nodes = root.findall('.//dependency')
        for dep in dep_nodes:
            group_id = dep.find('m:groupId', ns) or dep.find('groupId')
            artifact_id = dep.find('m:artifactId', ns) or dep.find('artifactId')
            version = dep.find('m:version', ns) or dep.find('version')
            if group_id is not None and artifact_id is not None:
                ver_text = version.text if version is not None else 'undefined'
                dep_info = {
                    'group': group_id.text,
                    'artifact': artifact_id.text,
                    'version': ver_text,
                    'source': pom_path,
                }
                deps.append(dep_info)
                if version is None or ver_text in ('undefined', None, ''):
                    issues.append({
                        'dependency': f"{group_id.text}:{artifact_id.text}",
                        'issue': 'No version specified',
                        'severity': 'major',
                        'source': pom_path,
                    })
    except Exception as e:
        issues.append({'file': pom_path, 'error': str(e), 'severity': 'major'})
    return deps, issues


async def analyze_maven(project_path: str) -> Dict:
    """Analyze Maven dependencies (multi-module)."""
    result = {
        'project_path': project_path,
        'build_tool': 'maven',
        'modules': [],
        'dependencies': [],
        'issues': [],
        'vulnerabilities': [],
        'version_conflicts': [],
    }

    pom_files = _find_all_build_files(project_path, ['pom.xml'])
    if not pom_files:
        return {'error': 'pom.xml not found'}

    # Aggregate across modules
    all_versions: Dict[str, List[Dict]] = {}  # artifact -> [{version, source}]
    for pom_path in pom_files:
        module = _module_name_from_path(pom_path, project_path)
        deps, issues = _parse_pom(pom_path)
        result['modules'].append({'name': module, 'file': pom_path, 'dependency_count': len(deps)})
        result['dependencies'].extend(deps)
        result['issues'].extend(issues)
        for dep in deps:
            key = f"{dep['group']}:{dep['artifact']}"
            all_versions.setdefault(key, []).append({'version': dep['version'], 'module': module})

    # Detect version conflicts
    for artifact, entries in all_versions.items():
        versions = {e['version'] for e in entries if e['version'] not in ('undefined', None, '')}
        if len(versions) > 1:
            result['version_conflicts'].append({
                'dependency': artifact,
                'versions': list(versions),
                'modules': [e['module'] for e in entries],
                'issue': f"Version conflict: {', '.join(sorted(versions))}",
                'severity': 'major',
            })

    # Parse properties from root pom
    try:
        tree = ET.parse(pom_files[0])
        root_el = tree.getroot()
        ns = {'m': 'http://maven.apache.org/POM/4.0.0'}
        properties = root_el.find('.//m:properties', ns)
        if properties is not None:
            result['properties'] = {
                child.tag.replace('{http://maven.apache.org/POM/4.0.0}', ''): child.text
                for child in properties
            }
    except Exception:
        pass

    return result


# ---------------------------------------------------------------------------
# Gradle
# ---------------------------------------------------------------------------
def _parse_gradle_file(gradle_file: str) -> Tuple[List[Dict], List[Dict]]:
    """Parse a single build.gradle and return (dependencies, issues)."""
    deps: List[Dict] = []
    issues: List[Dict] = []
    try:
        with open(gradle_file, 'r', encoding='utf-8') as f:
            content = f.read()
        deps_content = _extract_gradle_deps_block(content)
        if deps_content is None:
            return deps, issues
        for line in deps_content.split('\n'):
            line = line.strip()
            if not line or line.startswith('//'):
                continue
            match = re.match(
                r"(implementation|api|compile|testImplementation|runtimeOnly|compileOnly)"
                r"\s*['\"]([^'\":]+):([^'\":]+):([^'\"]+)['\"]",
                line
            )
            if match:
                deps.append({
                    'scope': match.group(1),
                    'group': match.group(2),
                    'artifact': match.group(3),
                    'version': match.group(4),
                    'source': gradle_file,
                })
            else:
                simple = re.match(
                    r"(implementation|api)\s*['\"]([^:]+):([^'\"]+)['\"]",
                    line
                )
                if simple:
                    deps.append({
                        'scope': simple.group(1),
                        'group': simple.group(2),
                        'artifact': simple.group(3),
                        'version': 'dynamic',
                        'source': gradle_file,
                    })
    except Exception as e:
        issues.append({'file': gradle_file, 'error': str(e)})
    return deps, issues


async def analyze_gradle(project_path: str) -> Dict:
    """Analyze Gradle dependencies (multi-module)."""
    result = {
        'project_path': project_path,
        'build_tool': 'gradle',
        'modules': [],
        'dependencies': [],
        'issues': [],
        'vulnerabilities': [],
        'version_conflicts': [],
    }

    gradle_files = _find_all_build_files(
        project_path, ['build.gradle', 'build.gradle.kts']
    )
    if not gradle_files:
        return {'error': 'No build.gradle found'}

    all_versions: Dict[str, List[Dict]] = {}
    for gradle_file in gradle_files:
        module = _module_name_from_path(gradle_file, project_path)
        deps, issues = _parse_gradle_file(gradle_file)
        result['modules'].append({'name': module, 'file': gradle_file, 'dependency_count': len(deps)})
        result['dependencies'].extend(deps)
        result['issues'].extend(issues)
        for dep in deps:
            key = f"{dep['group']}:{dep['artifact']}"
            all_versions.setdefault(key, []).append({'version': dep['version'], 'module': module})

    # Detect version conflicts
    for artifact, entries in all_versions.items():
        versions = {e['version'] for e in entries if e['version'] not in ('dynamic', None, '')}
        if len(versions) > 1:
            result['version_conflicts'].append({
                'dependency': artifact,
                'versions': list(versions),
                'modules': [e['module'] for e in entries],
                'issue': f"Version conflict: {', '.join(sorted(versions))}",
                'severity': 'major',
            })

    return result

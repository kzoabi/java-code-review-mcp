"""Dependency Analyzer Module - Maven/Gradle support"""
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional

async def analyze_dependencies(project_path: str, build_tool: str = 'auto') -> Dict:
    """Analyze Maven or Gradle dependencies."""
    result = {'project_path': project_path, 'build_tool': None, 'dependencies': [], 'issues': [], 'vulnerabilities': []}
    if build_tool == 'auto':
        if os.path.exists(os.path.join(project_path, 'pom.xml')):
            build_tool = 'maven'
        elif os.path.exists(os.path.join(project_path, 'build.gradle')) or os.path.exists(os.path.join(project_path, 'build.gradle.kts')):
            build_tool = 'gradle'
        else:
            return {'error': 'No Maven (pom.xml) or Gradle (build.gradle) found'}
    if build_tool == 'maven':
        return await analyze_maven(project_path)
    elif build_tool == 'gradle':
        return await analyze_gradle(project_path)
    return {'error': f'Unknown build tool: {build_tool}'}

async def analyze_maven(project_path: str) -> Dict:
    """Analyze Maven dependencies from pom.xml."""
    result = {'project_path': project_path, 'build_tool': 'maven', 'dependencies': [], 'issues': [], 'vulnerabilities': []}
    pom_path = os.path.join(project_path, 'pom.xml')
    if not os.path.exists(pom_path):
        return {'error': 'pom.xml not found'}
    try:
        tree = ET.parse(pom_path)
        root = tree.getroot()
        ns = {'m': 'http://maven.apache.org/POM/4.0.0'}
        deps = root.findall('.//m:dependency', ns)
        if not deps:
            deps = root.findall('.//dependency')
        for dep in deps:
            group_id = dep.find('m:groupId', ns) or dep.find('groupId')
            artifact_id = dep.find('m:artifactId', ns) or dep.find('artifactId')
            version = dep.find('m:version', ns) or dep.find('version')
            if group_id is not None and artifact_id is not None:
                dep_info = {'group': group_id.text, 'artifact': artifact_id.text, 'version': version.text if version is not None else 'undefined'}
                result['dependencies'].append(dep_info)
                if version is None or version.text == 'undefined':
                    result['issues'].append({'dependency': f"{group_id.text}:{artifact_id.text}", 'issue': 'No version specified', 'severity': 'major'})
        properties = root.find('.//m:properties', ns)
        if properties is not None:
            result['properties'] = {child.tag.replace('{http://maven.apache.org/POM/4.0.0}', ''): child.text for child in properties}
    except Exception as e:
        result['error'] = f'Error parsing pom.xml: {str(e)}'
    return result

async def analyze_gradle(project_path: str) -> Dict:
    """Analyze Gradle dependencies from build.gradle."""
    result = {'project_path': project_path, 'build_tool': 'gradle', 'dependencies': [], 'issues': [], 'vulnerabilities': []}
    gradle_files = []
    for fname in ['build.gradle', 'build.gradle.kts', 'app/build.gradle', 'app/build.gradle.kts']:
        fpath = os.path.join(project_path, fname)
        if os.path.exists(fpath):
            gradle_files.append(fpath)
    if not gradle_files:
        return {'error': 'No build.gradle found'}
    for gradle_file in gradle_files:
        try:
            with open(gradle_file, 'r', encoding='utf-8') as f:
                content = f.read()
            deps_block = re.search(r'dependencies\s*\{(.*?)\}', content, re.DOTALL)
            if deps_block:
                deps_content = deps_block.group(1)
                for line in deps_content.split('\n'):
                    line = line.strip()
                    if not line or line.startswith('//'):
                        continue
                    match = re.match(r"(implementation|api|compile|testImplementation|runtimeOnly)\s*['\"]([^'\":]+):([^'\":]+):([^'\"]+)['\"]", line)
                    if match:
                        result['dependencies'].append({'scope': match.group(1), 'group': match.group(2), 'artifact': match.group(3), 'version': match.group(4)})
                    elif 'implementation' in line or 'api' in line:
                        simple_match = re.match(r"(implementation|api)\s*['\"]([^:]+):([^']+)['\"]", line)
                        if simple_match:
                            result['dependencies'].append({'scope': simple_match.group(1), 'group': simple_match.group(2), 'artifact': simple_match.group(3), 'version': 'dynamic'})
        except Exception as e:
            result['issues'].append({'file': gradle_file, 'error': str(e)})
    return result

"""Architecture Analysis Module - Package structure and dependency validation"""
import os
import re
from typing import Dict, List, Any, Set, Tuple, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PackageInfo:
    name: str
    path: str
    is_domain: bool
    is_adapter: bool
    is_usecase: bool
    imports: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)


@dataclass
class ArchitectureIssue:
    severity: str
    category: str
    message: str
    suggestion: Optional[str] = None


def get_package_from_path(file_path: str) -> str:
    """Extract package name from Java file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        match = re.search(r'package\s+([\w.]+)\s*;', content)
        if match:
            return match.group(1)
    except:
        pass
    return ""


def is_domain_package(package: str, config: Dict) -> bool:
    """Check if package is a domain package."""
    domain_patterns = config.get('jbct_packages', {}).get('domain_patterns', [])
    for pattern in domain_patterns:
        pattern = pattern.replace('**', '')
        if pattern in package:
            return True
    return False


def is_adapter_package(package: str, config: Dict) -> bool:
    """Check if package is an adapter package."""
    adapter_patterns = config.get('jbct_packages', {}).get('adapter_patterns', [])
    for pattern in adapter_patterns:
        pattern = pattern.replace('**', '')
        if pattern in package:
            return True
    return False


def is_usecase_package(package: str) -> bool:
    """Check if package is a use case package."""
    return 'usecase' in package.lower() or 'service' in package.lower()


def extract_imports(content: str) -> List[str]:
    """Extract all import statements from Java file."""
    import_pattern = re.compile(r'import\s+([\w.]+)\.\w+;')
    return [match.group(1) for match in import_pattern.finditer(content)]


def analyze_package_structure(project_path: str, config: Dict) -> Dict:
    """Analyze package structure of a Java project."""
    result = {
        'packages': {},
        'issues': [],
        'summary': {
            'total_packages': 0,
            'domain_packages': 0,
            'adapter_packages': 0,
            'usecase_packages': 0
        }
    }
    
    java_files = []
    for root, dirs, files in os.walk(project_path):
        if 'target' in root or 'build' in root or '.git' in root:
            continue
        for file in files:
            if file.endswith('.java'):
                java_files.append(os.path.join(root, file))
    
    packages: Dict[str, PackageInfo] = {}
    
    for java_file in java_files:
        package = get_package_from_path(java_file)
        if not package:
            continue
        
        if package not in packages:
            packages[package] = PackageInfo(
                name=package,
                path=java_file,
                is_domain=is_domain_package(package, config),
                is_adapter=is_adapter_package(package, config),
                is_usecase=is_usecase_package(package)
            )
        
        try:
            with open(java_file, 'r', encoding='utf-8') as f:
                content = f.read()
            packages[package].imports.extend(extract_imports(content))
            
            class_pattern = re.compile(r'(?:public\s+)?(?:class|interface|record)\s+(\w+)')
            for match in class_pattern.finditer(content):
                packages[package].classes.append(match.group(1))
        except:
            pass
    
    result['packages'] = {k: {
        'name': v.name,
        'is_domain': v.is_domain,
        'is_adapter': v.is_adapter,
        'is_usecase': v.is_usecase,
        'imports': list(set(v.imports)),
        'classes': v.classes
    } for k, v in packages.items()}
    
    result['summary']['total_packages'] = len(packages)
    result['summary']['domain_packages'] = sum(1 for p in packages.values() if p.is_domain)
    result['summary']['adapter_packages'] = sum(1 for p in packages.values() if p.is_adapter)
    result['summary']['usecase_packages'] = sum(1 for p in packages.values() if p.is_usecase)
    
    return result


def check_circular_dependencies(project_path: str, config: Dict) -> Dict:
    """Check for circular dependencies between packages."""
    result = {
        'circular_dependencies': [],
        'issues': []
    }
    
    analysis = analyze_package_structure(project_path, config)
    packages = analysis.get('packages', {})
    
    def get_dependencies(pkg_name: str, visited: Set[str] = None) -> Set[str]:
        if visited is None:
            visited = set()
        
        if pkg_name in visited:
            return set()
        
        visited.add(pkg_name)
        deps = set()
        
        pkg_info = packages.get(pkg_name)
        if not pkg_info:
            return deps
        
        for imp in pkg_info.get('imports', []):
            imp_pkg = '.'.join(imp.split('.')[:-1])
            if imp_pkg in packages:
                deps.add(imp_pkg)
        
        return deps
    
    for pkg_name in packages:
        visited = set()
        stack = [(pkg_name, get_dependencies(pkg_name, {pkg_name}))]
        path = [pkg_name]
        
        while stack:
            current, deps = stack[-1]
            
            found_cycle = False
            for dep in deps:
                if dep in path:
                    cycle_start = path.index(dep)
                    cycle = path[cycle_start:] + [dep]
                    result['circular_dependencies'].append({
                        'package': dep,
                        'cycle': cycle,
                        'message': f"Circular dependency: {' -> '.join(cycle)}"
                    })
                    result['issues'].append({
                        'severity': 'error',
                        'category': 'circular-dependency',
                        'message': f"Circular dependency involving package '{dep}'",
                        'suggestion': f"Break the cycle: {' -> '.join(cycle)}"
                    })
                    found_cycle = True
                    break
                elif dep not in visited:
                    stack.append((dep, get_dependencies(dep, visited | {dep})))
                    path.append(dep)
                    found_cycle = True
                    break
            
            if not found_cycle:
                stack.pop()
                path.pop()
    
    return result


def check_import_flow(project_path: str, config: Dict) -> Dict:
    """Check for invalid import flows (domain should not depend on adapter)."""
    result = {
        'invalid_imports': [],
        'issues': []
    }
    
    analysis = analyze_package_structure(project_path, config)
    packages = analysis.get('packages', {})
    
    adapter_packages = {name for name, info in packages.items() if info.get('is_adapter', False)}
    domain_packages = {name for name, info in packages.items() if info.get('is_domain', False)}
    
    for pkg_name, pkg_info in packages.items():
        if not pkg_info.get('is_domain', False):
            continue
        
        for imp in pkg_info.get('imports', []):
            imp_pkg = '.'.join(imp.split('.')[:-1])
            
            if imp_pkg in adapter_packages:
                result['invalid_imports'].append({
                    'from_package': pkg_name,
                    'to_package': imp_pkg,
                    'import': imp
                })
                result['issues'].append({
                    'severity': 'error',
                    'category': 'import-flow',
                    'message': f"Domain package '{pkg_name}' imports adapter '{imp_pkg}'",
                    'suggestion': "Move adapter interface to domain package or use dependency injection"
                })
    
    return result


def check_package_structure(project_path: str, config: Dict) -> Dict:
    """Validate package structure matches JBCT architecture."""
    result = {
        'structure': {},
        'issues': [],
        'is_valid': True
    }
    
    expected_layers = {
        'domain': False,
        'adapter': False,
        'usecase': False
    }
    
    java_files = []
    for root, dirs, files in os.walk(project_path):
        if 'target' in root or 'build' in root or '.git' in root:
            continue
        for file in files:
            if file.endswith('.java'):
                java_files.append(os.path.join(root, file))
    
    for java_file in java_files:
        package = get_package_from_path(java_file)
        
        if 'domain' in package.lower():
            expected_layers['domain'] = True
        if 'adapter' in package.lower() or 'io' in package.lower():
            expected_layers['adapter'] = True
        if 'usecase' in package.lower() or 'service' in package.lower():
            expected_layers['usecase'] = True
    
    result['structure'] = expected_layers
    
    if not expected_layers['domain']:
        result['issues'].append({
            'severity': 'warning',
            'category': 'package-structure',
            'message': "No domain package found",
            'suggestion': "Create domain package (e.g., com.example.domain) for business logic"
        })
        result['is_valid'] = False
    
    if not expected_layers['adapter']:
        result['issues'].append({
            'severity': 'warning',
            'category': 'package-structure',
            'message': "No adapter package found",
            'suggestion': "Create adapter package (e.g., com.example.adapter) for I/O operations"
        })
        result['is_valid'] = False
    
    return result


async def analyze_architecture(project_path: str, config: Dict) -> Dict:
    """Run full architecture analysis on a project."""
    result = {
        'project_path': project_path,
        'package_structure': {},
        'circular_dependencies': [],
        'import_flow_issues': [],
        'issues': [],
        'summary': {}
    }
    
    structure = check_package_structure(project_path, config)
    result['package_structure'] = structure.get('structure', {})
    result['issues'].extend(structure.get('issues', []))
    
    circular = check_circular_dependencies(project_path, config)
    result['circular_dependencies'] = circular.get('circular_dependencies', [])
    result['issues'].extend(circular.get('issues', []))
    
    import_flow = check_import_flow(project_path, config)
    result['import_flow_issues'] = import_flow.get('invalid_imports', [])
    result['issues'].extend(import_flow.get('issues', []))
    
    error_count = sum(1 for i in result['issues'] if i.get('severity') == 'error')
    warning_count = sum(1 for i in result['issues'] if i.get('severity') == 'warning')
    
    result['summary'] = {
        'total_issues': len(result['issues']),
        'errors': error_count,
        'warnings': warning_count,
        'package_count': len(structure.get('structure', {}))
    }
    
    return result

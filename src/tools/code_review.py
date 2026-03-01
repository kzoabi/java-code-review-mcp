"""Code Review Module"""
import asyncio
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

async def review_file(file_path: str, review_level: str, config: Dict) -> Dict:
    """Review a single Java file."""
    if not os.path.exists(file_path):
        return {'error': f'File not found: {file_path}'}
    result = {'file_path': file_path, 'review_level': review_level, 'issues': [], 'suggestions': [], 'metrics': {}, 'jbct_issues': []}
    try:
        from src.tools.java_parser import analyze_java_file
        analysis = analyze_java_file(file_path)
        result['metrics'] = analysis['metrics']
        result['package'] = analysis['package']
        result['classes'] = analysis['classes']
        from src.tools.static_analysis import run_static_analysis
        static_result = await run_static_analysis(file_path, 'all', config)
        if 'issues' in static_result:
            result['issues'].extend(static_result['issues'])
        if static_result.get('jdk17_suggestions'):
            result['suggestions'].extend(static_result['jdk17_suggestions'])
        if static_result.get('jbct_issues'):
            result['jbct_issues'].extend(static_result['jbct_issues'])
    except Exception as e:
        result['error'] = str(e)
    return result

async def review_git_diff(repo_path: str, review_level: str, config: Dict) -> Dict:
    """Review uncommitted changes from git diff."""
    import subprocess
    result = {'repo_path': repo_path, 'review_level': review_level, 'files_reviewed': 0, 'issues': [], 'suggestions': []}
    try:
        diff_output = subprocess.run(['git', '-C', repo_path, 'diff'], capture_output=True, text=True)
        if diff_output.returncode != 0:
            return {'error': 'Not a git repository or no changes'}
        from src.tools.git_diff_parser import parse_git_diff
        changes = parse_git_diff(diff_output.stdout)
        for change in changes:
            if change['file_path'].endswith('.java'):
                temp_file = os.path.join(repo_path, change['file_path'])
                if os.path.exists(temp_file):
                    file_result = await review_file(temp_file, review_level, config)
                    if 'issues' in file_result:
                        result['issues'].extend(file_result['issues'])
                    if 'suggestions' in file_result:
                        result['suggestions'].extend(file_result['suggestions'])
                    result['files_reviewed'] += 1
    except Exception as e:
        result['error'] = str(e)
    return result

async def review_project(project_path: str, review_level: str, config: Dict, include_deps: bool = True) -> Dict:
    """Review an entire Java project."""
    result = {'project_path': project_path, 'review_level': review_level, 'files_reviewed': 0, 'issues': [], 'suggestions': [], 'dependencies': {}, 'summary': {}}
    java_files = []
    for root, dirs, files in os.walk(project_path):
        if 'target' in root or 'build' in root or '.git' in root or 'node_modules' in root:
            continue
        for file in files:
            if file.endswith('.java'):
                java_files.append(os.path.join(root, file))
    for java_file in java_files:
        file_result = await review_file(java_file, review_level, config)
        if 'issues' in file_result:
            result['issues'].extend(file_result['issues'])
        if 'suggestions' in file_result:
            result['suggestions'].extend(file_result['suggestions'])
        result['files_reviewed'] += 1
    if include_deps:
        from src.tools.dependency_analyzer import analyze_dependencies
        deps_result = await analyze_dependencies(project_path, 'auto')
        result['dependencies'] = deps_result
    issue_counts = {'critical': 0, 'major': 0, 'minor': 0}
    for issue in result['issues']:
        severity = issue.get('severity', 'minor')
        if severity in issue_counts:
            issue_counts[severity] += 1
    result['summary'] = {'total_files': result['files_reviewed'], 'total_issues': len(result['issues']), **issue_counts}
    return result


async def review_jbct_file(file_path: str, config: Dict) -> Dict:
    """Review a single Java file for JBCT methodology compliance."""
    if not os.path.exists(file_path):
        return {'error': f'File not found: {file_path}'}
    
    result = {
        'file_path': file_path,
        'jbct_profile': config.get('jbct_profile', 'disabled'),
        'issues': [],
        'summary': {'errors': 0, 'warnings': 0}
    }
    
    try:
        from src.tools.java_parser import parse_java_file
        analysis = parse_java_file(file_path)
        package = analysis.package or ""
    except:
        package = ""
    
    try:
        from src.tools.jbct_analyzer import run_jbct_analysis
        jbct_result = run_jbct_analysis(file_path, config, package)
        
        if 'issues' in jbct_result:
            result['issues'] = jbct_result['issues']
        if 'summary' in jbct_result:
            result['summary'] = jbct_result['summary']
            
    except Exception as e:
        result['error'] = str(e)
    
    return result


async def review_jbct_project(project_path: str, config: Dict) -> Dict:
    """Review entire project for JBCT methodology compliance."""
    result = {
        'project_path': project_path,
        'jbct_profile': config.get('jbct_profile', 'disabled'),
        'files_reviewed': 0,
        'issues': [],
        'summary': {'errors': 0, 'warnings': 0}
    }
    
    java_files = []
    for root, dirs, files in os.walk(project_path):
        if 'target' in root or 'build' in root or '.git' in root or 'node_modules' in root:
            continue
        for file in files:
            if file.endswith('.java'):
                java_files.append(os.path.join(root, file))
    
    for java_file in java_files:
        file_result = await review_jbct_file(java_file, config)
        if 'issues' in file_result:
            result['issues'].extend(file_result['issues'])
        result['files_reviewed'] += 1
    
    error_count = 0
    warning_count = 0
    for issue in result['issues']:
        if issue.get('severity') == 'error':
            error_count += 1
        else:
            warning_count += 1
    
    result['summary'] = {
        'total_files': result['files_reviewed'],
        'errors': error_count,
        'warnings': warning_count
    }
    
    return result

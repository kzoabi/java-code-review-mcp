"""Code Review Module"""
import asyncio
import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# ---------------------------------------------------------------------------
# Cache helpers (F9)
# ---------------------------------------------------------------------------
CACHE_FILENAME = '.java_review_cache.json'

def _cache_key(file_path: str, config: Dict) -> str:
    """Stable cache key for a file + config combination."""
    try:
        mtime = os.path.getmtime(file_path)
    except OSError:
        mtime = 0
    config_hash = hashlib.md5(json.dumps(config, sort_keys=True, default=str).encode()).hexdigest()[:8]
    return f"{file_path}::{mtime}::{config_hash}"


def _load_cache(project_path: str) -> Dict:
    cache_file = os.path.join(project_path, CACHE_FILENAME)
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def _save_cache(project_path: str, cache: Dict) -> None:
    cache_file = os.path.join(project_path, CACHE_FILENAME)
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache, f, default=str)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# File review (F7: pass review_level to static analysis)
# ---------------------------------------------------------------------------
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
        static_result = await run_static_analysis(file_path, 'all', config, review_level=review_level)
        if 'issues' in static_result:
            result['issues'].extend(static_result['issues'])
        if static_result.get('jdk17_suggestions'):
            result['suggestions'].extend(static_result['jdk17_suggestions'])
        if static_result.get('jbct_issues'):
            result['jbct_issues'].extend(static_result['jbct_issues'])
    except Exception as e:
        result['error'] = str(e)
    return result


# ---------------------------------------------------------------------------
# Git diff review (F4: ref + staged params)
# ---------------------------------------------------------------------------
async def review_git_diff(repo_path: str, review_level: str, config: Dict,
                           ref: str = "", staged: bool = False) -> Dict:
    """Review changes from git diff.

    Args:
        ref:    Compare against a git ref (e.g. HEAD~1, main, a commit SHA).
                Mutually exclusive with staged.
        staged: When True, review only staged changes (git diff --cached).
    """
    result = {'repo_path': repo_path, 'review_level': review_level,
              'files_reviewed': 0, 'issues': [], 'suggestions': []}
    try:
        git_args = ['git', '-C', repo_path, 'diff']
        if staged:
            git_args.append('--cached')
        elif ref:
            git_args.append(ref)

        proc = await asyncio.create_subprocess_exec(
            *git_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
        stdout, _ = await proc.communicate()
        if proc.returncode != 0:
            return {'error': 'Not a git repository or no changes'}
        from src.tools.git_diff_parser import parse_git_diff
        changes = parse_git_diff(stdout.decode('utf-8', errors='replace'))
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


# ---------------------------------------------------------------------------
# Project review (F5: architecture analysis; F9: file cache)
# ---------------------------------------------------------------------------
async def review_project(project_path: str, review_level: str, config: Dict,
                          include_deps: bool = True, use_cache: bool = True) -> Dict:
    """Review an entire Java project."""
    result = {
        'project_path': project_path,
        'review_level': review_level,
        'files_reviewed': 0,
        'issues': [],
        'suggestions': [],
        'dependencies': {},
        'architecture_issues': [],
        'package_structure': {},
        'circular_dependencies': [],
        'import_flow_issues': [],
        'summary': {}
    }

    java_files = []
    for root, dirs, files in os.walk(project_path):
        if 'target' in root or 'build' in root or '.git' in root or 'node_modules' in root:
            continue
        for file in files:
            if file.endswith('.java'):
                java_files.append(os.path.join(root, file))

    cache = _load_cache(project_path) if use_cache else {}
    cache_updated = False

    for java_file in java_files:
        key = _cache_key(java_file, config)
        if use_cache and key in cache:
            cached = cache[key]
            result['issues'].extend(cached.get('issues', []))
            result['suggestions'].extend(cached.get('suggestions', []))
        else:
            file_result = await review_file(java_file, review_level, config)
            if 'issues' in file_result:
                result['issues'].extend(file_result['issues'])
            if 'suggestions' in file_result:
                result['suggestions'].extend(file_result['suggestions'])
            if use_cache:
                cache[key] = {
                    'issues': file_result.get('issues', []),
                    'suggestions': file_result.get('suggestions', []),
                }
                cache_updated = True
        result['files_reviewed'] += 1

    if use_cache and cache_updated:
        _save_cache(project_path, cache)

    if include_deps:
        from src.tools.dependency_analyzer import analyze_dependencies
        deps_result = await analyze_dependencies(project_path, 'auto')
        result['dependencies'] = deps_result

    # F5: Run architecture analysis and merge into project result
    try:
        from src.tools.architecture_analyzer import analyze_architecture
        arch_result = await analyze_architecture(project_path, config)
        result['architecture_issues'] = arch_result.get('issues', [])
        result['package_structure'] = arch_result.get('package_structure', {})
        result['circular_dependencies'] = arch_result.get('circular_dependencies', [])
        result['import_flow_issues'] = arch_result.get('import_flow_issues', [])
    except Exception as e:
        result['architecture_error'] = str(e)

    issue_counts = {'critical': 0, 'major': 0, 'minor': 0}
    for issue in result['issues']:
        severity = issue.get('severity', 'minor')
        if severity in issue_counts:
            issue_counts[severity] += 1
    result['summary'] = {
        'total_files': result['files_reviewed'],
        'total_issues': len(result['issues']),
        'architecture_issues': len(result['architecture_issues']),
        **issue_counts
    }
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
    except Exception:
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
    
    file_errors = []
    for java_file in java_files:
        file_result = await review_jbct_file(java_file, config)
        if 'error' in file_result:
            file_errors.append({'file': java_file, 'error': file_result['error']})
            continue
        if 'issues' in file_result:
            result['issues'].extend(file_result['issues'])
        result['files_reviewed'] += 1
    if file_errors:
        result['errors'] = file_errors
    
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

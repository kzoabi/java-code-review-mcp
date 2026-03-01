"""Static Analysis Module - Pure Python implementation"""
import re
import os
from typing import Dict, List, Any
from pathlib import Path

MAGIC_NUMBER_PATTERN = re.compile(r'\b\d{3,}\b')
SENSITIVE_PATTERNS = [re.compile(r'password\s*=', re.I), re.compile(r'api[_-]?key\s*=', re.I), re.compile(r'secret\s*=', re.I), re.compile(r'token\s*=', re.I), re.compile(r'private[_-]?key\s*=', re.I)]
SQL_PATTERNS = [re.compile(r'\bexecute\s*\(\s*["\'].*\+', re.I), re.compile(r'\bcreateStatement\s*\(\s*\)', re.I)]

async def run_static_analysis(file_path: str, tools: str, config: Dict) -> Dict:
    """Run static analysis on a Java file."""
    result = {'file_path': file_path, 'issues': [], 'jdk17_suggestions': [], 'jbct_issues': []}
    if not os.path.exists(file_path):
        return {'error': f'File not found: {file_path}'}
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    max_line_length = config.get('max_line_length', 120)
    max_method_length = config.get('max_method_length', 30)
    max_class_length = config.get('max_class_length', 500)
    max_parameters = config.get('max_parameters', 5)
    for i, line in enumerate(lines, 1):
        if len(line) > max_line_length:
            result['issues'].append({'line': i, 'severity': 'minor', 'category': 'style', 'message': f'Line exceeds {max_line_length} characters', 'rule': 'LineLength'})
        if re.search(r'System\.out\.print', line) and 'logger' not in line.lower():
            result['issues'].append({'line': i, 'severity': 'minor', 'category': 'best-practice', 'message': 'Use logger instead of System.out.print', 'rule': 'UseLogger'})
        for pattern in SENSITIVE_PATTERNS:
            if pattern.search(line):
                result['issues'].append({'line': i, 'severity': 'critical', 'category': 'security', 'message': 'Potential hardcoded credential detected', 'rule': 'HardcodedCredentials'})
        for pattern in SQL_PATTERNS:
            if pattern.search(line):
                result['issues'].append({'line': i, 'severity': 'critical', 'category': 'security', 'message': 'Potential SQL injection risk', 'rule': 'SQLInjection'})
    try:
        from src.tools.java_parser import parse_java_file, extract_class_info
        analysis = parse_java_file(file_path)
        for cls in analysis.classes:
            class_length = cls.end_line - cls.start_line + 1
            if class_length > max_class_length:
                result['issues'].append({'line': cls.start_line, 'severity': 'major', 'category': 'design', 'message': f"Class '{cls.name}' exceeds {max_class_length} lines", 'rule': 'ClassLength'})
            for method in cls.methods:
                if method.body_lines > max_method_length:
                    result['issues'].append({'line': method.start_line, 'severity': 'major', 'category': 'design', 'message': f"Method '{method.name}' exceeds {max_method_length} lines", 'rule': 'MethodLength'})
                if len(method.parameters) > max_parameters:
                    result['issues'].append({'line': method.start_line, 'severity': 'major', 'category': 'design', 'message': f"Method '{method.name}' has too many parameters ({len(method.parameters)})", 'rule': 'TooManyParameters'})
            if not cls.is_record:
                dto_candidates = [f for f in cls.fields if f.get('initializers') == False and len(cls.methods) <= 3]
                if dto_candidates and config.get('jdk17_features', {}).get('recommend_records', True):
                    result['jdk17_suggestions'].append({'line': cls.start_line, 'category': 'jdk17', 'message': f"Class '{cls.name}' could be a Java 17 Record", 'suggestion': 'Consider converting to record for immutable DTO'})
            if 'extends' not in cls.modifiers and 'abstract' not in cls.modifiers and len(cls.fields) > 0:
                if config.get('jdk17_features', {}).get('recommend_sealed_classes', True):
                    has_subclasses = False
                    for other_cls in analysis.classes:
                        if other_cls.extends == cls.name:
                            has_subclasses = True
                            break
                    if has_subclasses:
                        result['jdk17_suggestions'].append({'line': cls.start_line, 'category': 'jdk17', 'message': f"Class '{cls.name}' has subclasses - consider Sealed class", 'suggestion': 'Use sealed class for controlled inheritance'})
        catch_blocks = re.findall(r'catch\s*\([^)]+\)\s*\{[^}]*\}', content, re.DOTALL)
        for block in catch_blocks:
            if 'catch' in block and re.search(r'catch\s*\([^)]*\)\s*\{\s*\}', block):
                result['issues'].append({'line': 1, 'severity': 'major', 'category': 'exception', 'message': 'Empty catch block', 'rule': 'EmptyCatchBlock'})
        if config.get('jdk17_features', {}).get('recommend_switch_expressions', True):
            if re.search(r'switch\s*\([^)]+\)\s*\{', content) and '->' not in content:
                result['jdk17_suggestions'].append({'line': 1, 'category': 'jdk17', 'message': 'Traditional switch statement found', 'suggestion': 'Consider using switch expressions (Java 14+)'})
        if config.get('jdk17_features', {}).get('recommend_text_blocks', True):
            if re.search(r'String\s+\w+\s*=\s*"[^"]*\n', content):
                result['jdk17_suggestions'].append({'line': 1, 'category': 'jdk17', 'message': 'Multiline string concatenation found', 'suggestion': 'Consider using Text Blocks (Java 15+)'})
        if config.get('jdk17_features', {}).get('recommend_var_keyword', True):
            for i, line in enumerate(lines, 1):
                if re.match(r'\s*(private|public|protected)?\s*(static)?\s*\w+\s+\w+\s*=', line):
                    if 'var' not in line and 'List<' in line:
                        result['jdk17_suggestions'].append({'line': i, 'category': 'jdk17', 'message': 'Type can be replaced with var', 'suggestion': 'Use var for local variable type inference'})
        if config.get('jdk17_features', {}).get('recommend_pattern_matching', True):
            for i, line in enumerate(lines, 1):
                if re.search(r'instanceof\s+\w+\s*\)', line) and 'String s' not in line and 'Object o' not in line:
                    result['jdk17_suggestions'].append({'line': i, 'category': 'jdk17', 'message': 'instanceof pattern match', 'suggestion': 'Use pattern matching for instanceof (Java 16+)'})
    except Exception as e:
        result['parse_error'] = str(e)
    
    jbct_profile = config.get('jbct_profile', 'disabled')
    if jbct_profile != 'disabled':
        try:
            from src.tools.jbct_analyzer import run_jbct_analysis
            package = ""
            try:
                from src.tools.java_parser import parse_java_file
                analysis = parse_java_file(file_path)
                package = analysis.package or ""
            except:
                pass
            
            jbct_result = run_jbct_analysis(file_path, config, package)
            if 'issues' in jbct_result:
                result['jbct_issues'] = jbct_result['issues']
        except Exception as e:
            result['jbct_error'] = str(e)
    
    return result

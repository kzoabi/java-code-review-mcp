"""Java Parser Module"""
import javalang
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field

@dataclass
class MethodInfo:
    name: str
    return_type: str
    parameters: List[Tuple[str, str]]
    modifiers: List[str]
    body_lines: int
    start_line: int
    end_line: int
    exceptions: List[str] = field(default_factory=list)
    is_constructor: bool = False

@dataclass
class ClassInfo:
    name: str
    modifiers: List[str]
    extends: Optional[str]
    implements: List[str]
    fields: List[Dict[str, Any]]
    methods: List[MethodInfo]
    start_line: int
    end_line: int
    is_record: bool = False
    is_sealed: bool = False
    permits: List[str] = field(default_factory=list)

@dataclass
class ImportInfo:
    name: str
    is_static: bool
    is_on_demand: bool

@dataclass
class JavaFileAnalysis:
    file_path: str
    package: Optional[str]
    imports: List[ImportInfo]
    classes: List[ClassInfo]
    total_lines: int
    code_lines: int
    comment_lines: int
    blank_lines: int
    raw_tree: Any = None

def parse_java_file(file_path: str) -> JavaFileAnalysis:
    with open(file_path, 'r', encoding='utf-8') as f:
        source_code = f.read()
    return parse_java_source(file_path, source_code)

def find_end_line(lines: List[str], start_line: int) -> int:
    """Scan forward from start_line (1-indexed) counting braces to find the closing }."""
    depth = 0
    for i in range(start_line - 1, len(lines)):
        for ch in lines[i]:
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return i + 1  # 1-indexed
    return len(lines)

def parse_java_source(file_path: str, source_code: str) -> JavaFileAnalysis:
    lines = source_code.split('\n')
    total_lines = len(lines)
    comment_lines = 0
    blank_lines = 0
    in_block_comment = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('/*'):
            in_block_comment = True
            comment_lines += 1
        elif in_block_comment:
            comment_lines += 1
            if '*/' in stripped:
                in_block_comment = False
        elif stripped.startswith('//'):
            comment_lines += 1
        elif not stripped:
            blank_lines += 1
    code_lines = total_lines - comment_lines - blank_lines
    try:
        tree = javalang.parse.parse(source_code)
    except javalang.parser.JavaSyntaxError as e:
        raise ValueError(f"Syntax error: {e}")
    package = tree.package.name if tree.package else None
    imports = []
    for imp in tree.imports:
        name = imp.path if hasattr(imp, 'path') else (imp.children[0] if imp.children else '')
        imports.append(ImportInfo(name=name, is_static=imp.static, is_on_demand=imp.wildcard))
    classes = []
    for path, node in tree.filter(javalang.tree.ClassDeclaration):
        class_info = extract_class_info(node, lines)
        classes.append(class_info)
    return JavaFileAnalysis(file_path=file_path, package=package, imports=imports, classes=classes, total_lines=total_lines, code_lines=code_lines, comment_lines=comment_lines, blank_lines=blank_lines, raw_tree=tree)

def extract_class_info(node: javalang.tree.ClassDeclaration, lines: List[str]) -> ClassInfo:
    methods = []
    fields = []
    for child_path, child_node in node.filter(javalang.tree.MethodDeclaration):
        m_start = child_node.position.line if child_node.position else 0
        m_end = find_end_line(lines, m_start) if m_start else 0
        method_info = MethodInfo(name=child_node.name, return_type=str(child_node.return_type) if child_node.return_type else 'void', parameters=[(p.name, str(p.type)) for p in child_node.parameters], modifiers=list(child_node.modifiers), body_lines=len(child_node.body) if child_node.body else 0, start_line=m_start, end_line=m_end, exceptions=[str(e) for e in child_node.throws] if child_node.throws else [])
        methods.append(method_info)
    for child_path, child_node in node.filter(javalang.tree.FieldDeclaration):
        for var in child_node.declarators:
            fields.append({'name': var.name, 'type': str(child_node.type), 'modifiers': list(child_node.modifiers), 'initializers': var.initializer is not None})
    extends = str(node.extends) if node.extends else None
    implements = [str(i) for i in node.implements] if node.implements else []
    is_record = 'record' in node.modifiers
    is_sealed = 'sealed' in node.modifiers
    c_start = node.position.line if node.position else 0
    c_end = find_end_line(lines, c_start) if c_start else 0
    return ClassInfo(name=node.name, modifiers=list(node.modifiers), extends=extends, implements=implements, fields=fields, methods=methods, start_line=c_start, end_line=c_end, is_record=is_record, is_sealed=is_sealed)

def analyze_java_file(file_path: str) -> Dict[str, Any]:
    analysis = parse_java_file(file_path)
    result = {'file_path': file_path, 'package': analysis.package, 'imports': [imp.name for imp in analysis.imports], 'classes': [], 'metrics': {'total_lines': analysis.total_lines, 'code_lines': analysis.code_lines, 'comment_lines': analysis.comment_lines, 'blank_lines': analysis.blank_lines}, 'issues': []}
    for cls in analysis.classes:
        class_data = {'name': cls.name, 'is_record': cls.is_record, 'is_sealed': cls.is_sealed, 'extends': cls.extends, 'implements': cls.implements, 'permits': cls.permits, 'modifiers': cls.modifiers, 'fields_count': len(cls.fields), 'methods_count': len(cls.methods), 'lines': cls.end_line - cls.start_line + 1, 'methods': []}
        for method in cls.methods:
            class_data['methods'].append({'name': method.name, 'return_type': method.return_type, 'parameters': method.parameters, 'modifiers': method.modifiers, 'lines': method.body_lines, 'exceptions': method.exceptions, 'is_constructor': method.is_constructor})
        result['classes'].append(class_data)
    return result

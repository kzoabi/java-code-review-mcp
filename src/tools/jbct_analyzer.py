"""JBCT Analyzer Module - JBCT Methodology Compliance Checks"""
import os
import re
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field

PRAGMATICA_IMPORTS = {
    'org.pragmatica.lang.Option',
    'org.pragmatica.lang.Result',
    'org.pragmatica.lang.Promise',
    'org.pragmatica.lang.Cause',
    'org.pragmatica.lang.Verify',
    'org.pragmatica.lang.Promise',
    'org.pragmatica.lang.Result',
    'org.pragmatica.lang.Unit'
}

IO_IMPORTS = {
    'java.io',
    'java.nio.file',
    'java.net.http'
}

EXCEPTION_IMPORTS = {
    'java.lang.Exception',
    'java.lang.RuntimeException',
    'java.lang.Error'
}

ZONE2_VERBS = {'validate', 'process', 'handle', 'execute', 'perform', 'transform', 'create', 'update', 'delete', 'save'}
ZONE3_VERBS = {'get', 'fetch', 'load', 'parse', 'convert', 'find', 'query', 'read', 'write', 'check', 'exists'}


@dataclass
class JBCTRuleIssue:
    rule: str
    severity: str
    category: str
    line: int
    message: str
    suggestion: Optional[str] = None


def is_domain_package(package: str, config: Dict) -> bool:
    """Check if package is a domain package."""
    domain_patterns = config.get('jbct_packages', {}).get('domain_patterns', [])
    for pattern in domain_patterns:
        pattern = pattern.replace('**', '')
        if pattern in package:
            return True
    return False


def check_return_types(content: str, lines: List[str], config: Dict) -> List[JBCTRuleIssue]:
    """JBCT-RET-01: Business methods must use T, Option, Result, or Promise.
       JBCT-RET-03: Never return null - use Option<T>."""
    issues = []
    
    throws_pattern = re.compile(r'throws\s+\w+')
    return_null_pattern = re.compile(r'return\s+null\s*;')
    
    method_pattern = re.compile(
        r'(?:public|private|protected)?\s*(?:static)?\s*(?:final)?\s*(\w+(?:<[^>]+>)?)\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+[^{]+)?\{',
        re.MULTILINE
    )
    
    for match in method_pattern.finditer(content):
        return_type = match.group(1)
        method_name = match.group(2)
        start_pos = match.start()
        
        line_num = content[:start_pos].count('\n') + 1
        
        if return_type in ['void', 'Void']:
            line_content = lines[line_num - 1] if line_num <= len(lines) else ""
            if throws_pattern.search(line_content):
                issues.append(JBCTRuleIssue(
                    rule='JBCT-RET-01',
                    severity='error',
                    category='return-types',
                    line=line_num,
                    message=f"Method '{method_name}' can throw but returns void - use Result or Promise",
                    suggestion="Return Result<T> or Promise<T> instead of void when method can fail"
                ))
        
        if return_null_pattern.search(content[match.end():match.end() + 100]):
            issues.append(JBCTRuleIssue(
                rule='JBCT-RET-03',
                severity='error',
                category='return-types',
                line=line_num,
                message=f"Method '{method_name}' returns null - use Option<T> instead",
                suggestion="Return Option<T> to explicitly represent optional values"
            ))
    
    return issues


def check_exceptions(content: str, lines: List[str], config: Dict) -> List[JBCTRuleIssue]:
    """JBCT-EX-01: No business exceptions - use Cause with Result/Promise."""
    issues = []
    
    throw_pattern = re.compile(r'\bthrow\s+new\s+(\w+(?:Exception|Error))')
    throws_clause_pattern = re.compile(r'throws\s+(\w+(?:Exception|Error))')
    
    for i, line in enumerate(lines, 1):
        if throw_pattern.search(line) and 'Test' not in line and 'test' not in line.lower():
            match = throw_pattern.search(line)
            exc_class = match.group(1) if match else "Exception"
            if exc_class not in ['AssertionError', 'UnsupportedOperationException']:
                issues.append(JBCTRuleIssue(
                    rule='JBCT-EX-01',
                    severity='error',
                    category='exceptions',
                    line=i,
                    message=f"Business exception '{exc_class}' - use Cause with Result/Promise instead",
                    suggestion="Replace with Result.failure(Cause.cause(...)) or Promise.failure(Cause.cause(...))"
                ))
        
        if throws_clause_pattern.search(line):
            issues.append(JBCTRuleIssue(
                rule='JBCT-EX-01',
                severity='error',
                category='exceptions',
                line=i,
                message="Method throws exception - use Result or Promise for error handling",
                suggestion="Remove throws clause and return Result<T> or Promise<T> instead"
            ))
    
    return issues


def check_value_objects(content: str, lines: List[str], config: Dict) -> List[JBCTRuleIssue]:
    """JBCT-VO-01: Value objects should have factory method returning Result<T>.
       JBCT-VO-02: Don't bypass factory - no direct constructor calls."""
    issues = []
    
    record_pattern = re.compile(r'record\s+(\w+)\s*\(')
    class_pattern = re.compile(r'(?:public|private|protected)?\s*(?:final)?\s*class\s+(\w+)\s*\{')
    
    factory_pattern = re.compile(r'public\s+static\s+\w+(?:<[^>]+>)?\s+(\w+)\s*\(')
    
    direct_constructor_pattern = re.compile(r'new\s+(\w+)\s*\(')
    
    has_pragmatica = any(imp in content for imp in PRAGMATICA_IMPORTS)
    
    for match in record_pattern.finditer(content):
        record_name = match.group(1)
        start_pos = match.start()
        line_num = content[:start_pos].count('\n') + 1
        
        has_factory = False
        search_start = match.end()
        search_end = search_start + 2000
        search_content = content[search_start:search_end] if search_start < len(content) else ""
        
        for factory_match in factory_pattern.finditer(search_content):
            if factory_match.group(1).lower() == record_name.lower():
                has_factory = True
                break
        
        if not has_factory and has_pragmatica:
            issues.append(JBCTRuleIssue(
                rule='JBCT-VO-01',
                severity='warning',
                category='value-objects',
                line=line_num,
                message=f"Record '{record_name}' should have a static factory method returning Result<{record_name}>",
                suggestion=f"Add: public static Result<{record_name}> {record_name.lower()}(...) {{ ... }}"
            ))
    
    for i, line in enumerate(lines, 1):
        for match in direct_constructor_pattern.finditer(line):
            class_name = match.group(1)
            if class_name[0].isupper() and class_name not in ['ArrayList', 'HashMap', 'HashSet', 'List', 'Map', 'Set', 'Optional', 'String', 'Integer', 'Long', 'Boolean', 'Object']:
                if 'new ' + class_name in line and 'return new' not in line.lower() and 'factory' not in line.lower():
                    issues.append(JBCTRuleIssue(
                        rule='JBCT-VO-02',
                        severity='warning',
                        category='value-objects',
                        line=i,
                        message=f"Direct constructor call for '{class_name}' - use factory method instead",
                        suggestion=f"Use {class_name}.{class_name.lower()}(...) factory method if available"
                    ))
    
    return issues


def check_lambda_rules(content: str, lines: List[str], config: Dict) -> List[JBCTRuleIssue]:
    """JBCT-LAM-01: No complex logic in lambdas (if, switch, try-catch).
       JBCT-LAM-02: No braces in lambdas - extract to methods."""
    issues = []
    
    lambda_pattern = re.compile(r'(\w+)\s*->\s*\{([^}]+)\}')
    
    for i, line in enumerate(lines, 1):
        for match in lambda_pattern.finditer(line):
            lambda_body = match.group(2)
            
            if re.search(r'\bif\s*\(', lambda_body) or re.search(r'\bswitch\s*\(', lambda_body):
                issues.append(JBCTRuleIssue(
                    rule='JBCT-LAM-01',
                    severity='warning',
                    category='lambda',
                    line=i,
                    message="Complex logic (if/switch) in lambda - extract to named method",
                    suggestion="Extract conditional logic to a separate method and use method reference"
                ))
            
            if re.search(r'\btry\s*\{', lambda_body) or re.search(r'\bcatch\s*\(', lambda_body):
                issues.append(JBCTRuleIssue(
                    rule='JBCT-LAM-01',
                    severity='warning',
                    category='lambda',
                    line=i,
                    message="Try-catch in lambda - use Result.recover() instead",
                    suggestion="Use .recover() method on Result/Promise for error handling"
                ))
            
            if lambda_body.count('{') > 1 or lambda_body.count(';') > 1:
                issues.append(JBCTRuleIssue(
                    rule='JBCT-LAM-02',
                    severity='warning',
                    category='lambda',
                    line=i,
                    message="Multi-statement lambda body - extract to named method",
                    suggestion="Extract complex lambda body to a separate method"
                ))
    
    return issues


def check_patterns(content: str, lines: List[str], config: Dict) -> List[JBCTRuleIssue]:
    """JBCT-PAT-01: Use functional iteration instead of raw for/while loops."""
    issues = []
    
    traditional_loop_pattern = re.compile(r'\b(for|while)\s*\([^)]+\)\s*\{')
    
    stream_import = 'java.util.stream' in content
    
    for i, line in enumerate(lines, 1):
        if traditional_loop_pattern.search(line):
            match = traditional_loop_pattern.search(line)
            loop_type = match.group(1) if match else "loop"
            if stream_import:
                issues.append(JBCTRuleIssue(
                    rule='JBCT-PAT-01',
                    severity='warning',
                    category='patterns',
                    line=i,
                    message=f"Traditional {loop_type} loop - use stream/iterator instead",
                    suggestion="Use .stream().map(), .filter(), .forEach() or enhanced for-loop"
                ))
            else:
                issues.append(JBCTRuleIssue(
                    rule='JBCT-PAT-01',
                    severity='warning',
                    category='patterns',
                    line=i,
                    message=f"Traditional {loop_type} loop - consider functional iteration",
                    suggestion="Consider using streams or enhanced for-loop for better readability"
                ))
    
    return issues


def check_architecture(content: str, lines: List[str], config: Dict, package: str) -> List[JBCTRuleIssue]:
    """JBCT-MIX-01: No I/O operations in domain packages."""
    issues = []
    
    if not is_domain_package(package, config):
        return issues
    
    io_operation_patterns = [
        (r'\bFileReader\b', 'FileReader'),
        (r'\bFileWriter\b', 'FileWriter'),
        (r'\bBufferedReader\b', 'BufferedReader'),
        (r'\bBufferedWriter\b', 'BufferedWriter'),
        (r'\bFileInputStream\b', 'FileInputStream'),
        (r'\bFileOutputStream\b', 'FileOutputStream'),
        (r'\bPaths\.get\b', 'Paths.get'),
        (r'\bFiles\.(read|write|list|walk)\b', 'Files I/O'),
        (r'\bURL\s+', 'URL connection'),
        (r'\bHttpClient\b', 'HttpClient'),
        (r'\bConnection\b', 'Database connection'),
        (r'\bStatement\b', 'SQL Statement'),
        (r'\bPreparedStatement\b', 'SQL PreparedStatement'),
    ]
    
    for i, line in enumerate(lines, 1):
        for pattern, op_name in io_operation_patterns:
            if re.search(pattern, line):
                issues.append(JBCTRuleIssue(
                    rule='JBCT-MIX-01',
                    severity='error',
                    category='architecture',
                    line=i,
                    message=f"I/O operation '{op_name}' in domain package - move to adapter",
                    suggestion=f"Move I/O to adapter layer: adapter/{op_name.lower()}.java"
                ))
    
    return issues


def check_naming(content: str, lines: List[str], config: Dict) -> List[JBCTRuleIssue]:
    """JBCT-NAM-01: Factory methods TypeName.typeName().
       JBCT-NAM-02: Use Valid prefix, not Validated."""
    issues = []
    
    factory_pattern = re.compile(r'public\s+static\s+(?:final\s+)?(\w+)\s+(\w+)\s*\(')
    
    validated_pattern = re.compile(r'(?:record|class)\s+(Validated\w+)')
    valid_pattern = re.compile(r'(?:record|class)\s+(Valid\w+)')
    
    for match in factory_pattern.finditer(content):
        type_name = match.group(1)
        method_name = match.group(2)
        
        if method_name.lower() != type_name.lower() and not method_name.lower().startswith('of'):
            issues.append(JBCTRuleIssue(
                rule='JBCT-NAM-01',
                severity='warning',
                category='naming',
                line=content[:match.start()].count('\n') + 1,
                message=f"Factory method should be named '{type_name.lower()}' not '{method_name}'",
                suggestion=f"Rename to: public static {type_name} {type_name.lower()}(...)"
            ))
    
    for match in validated_pattern.finditer(content):
        class_name = match.group(1)
        start_pos = match.start()
        line_num = content[:start_pos].count('\n') + 1
        issues.append(JBCTRuleIssue(
            rule='JBCT-NAM-02',
            severity='warning',
            category='naming',
            line=line_num,
            message=f"Class '{class_name}' uses 'Validated' prefix - use 'Valid' instead",
            suggestion=f"Rename to: Valid{class_name[9:]}"
        ))
    
    return issues


def check_zones(content: str, lines: List[str], config: Dict, package: str) -> List[JBCTRuleIssue]:
    """JBCT-ZONE-01: Step interfaces use Zone 2 verbs.
       JBCT-ZONE-02: Leaf functions use Zone 3 verbs.
       JBCT-ZONE-03: No zone mixing in sequencer chains."""
    issues = []
    
    zone2_verbs = set(config.get('zone2_verbs', ['validate', 'process', 'handle', 'execute', 'perform', 'transform']))
    zone3_verbs = set(config.get('zone3_verbs', ['get', 'fetch', 'load', 'parse', 'convert', 'find', 'query']))
    
    is_domain = is_domain_package(package, config)
    
    interface_pattern = re.compile(r'(?:public\s+)?interface\s+(\w+)')
    method_pattern = re.compile(r'(?:default\s+)?(\w+)\s*\([^)]*\)\s*(?::\s*\w+)?\s*;')
    
    for match in interface_pattern.finditer(content):
        interface_name = match.group(1)
        is_step_interface = any(verb in interface_name.lower() for verb in ['step', 'usecase', 'service'])
        
        if is_step_interface:
            search_start = match.end()
            search_content = content[search_start:search_start + 3000]
            
            for method_match in method_pattern.finditer(search_content):
                method_name = method_match.group(1)
                method_line = content[:match.start() + method_match.start()].count('\n') + 1
                
                if method_name.lower() in zone3_verbs:
                    issues.append(JBCTRuleIssue(
                        rule='JBCT-ZONE-01',
                        severity='warning',
                        category='zones',
                        line=method_line,
                        message=f"Step interface method '{method_name}' uses Zone 3 verb - use Zone 2 verb",
                        suggestion=f"Use Zone 2 verb: validate, process, handle, execute, perform, transform"
                    ))
    
    leaf_method_pattern = re.compile(r'(?:private|public|protected)?\s*(?:static)?\s*\w+(?:<[^>]+>)?\s+((?:get|fetch|load|parse|convert|find|query)\w*)\s*\([^)]*\)\s*(?:throws\s+[^{]+)?\{')
    
    for match in leaf_method_pattern.finditer(content):
        method_name = match.group(1)
        line_num = content[:match.start()].count('\n') + 1
        
        if any(method_name.lower().startswith(v) for v in zone3_verbs):
            if is_domain:
                issues.append(JBCTRuleIssue(
                    rule='JBCT-ZONE-02',
                    severity='warning',
                    category='zones',
                    line=line_num,
                    message=f"Leaf method '{method_name}' in domain uses Zone 3 verb - appropriate for leaf",
                    suggestion="Zone 3 verbs (get, fetch, parse) are correct for leaf/adapter methods"
                ))
    
    sequencer_pattern = re.compile(r'\.(?:flatMap|map)\s*\([^)]+\.(?:flatMap|map)')
    if sequencer_pattern.search(content):
        issues.append(JBCTRuleIssue(
            rule='JBCT-ZONE-03',
            severity='warning',
            category='zones',
            line=1,
            message="Zone mixing detected in sequencer chain",
            suggestion="Avoid mixing different zone types in flatMap/map chains"
        ))
    
    return issues


def check_return_types_2(content: str, lines: List[str], config: Dict) -> List[JBCTRuleIssue]:
    """JBCT-RET-02: No nested wrappers (Promise<Result<T>>, Option<Option<T>>).
       JBCT-RET-04: Use Unit instead of Void.
        JBCT-RET-05: Avoid always-succeeding Result (return T directly)."""
    issues = []
    
    nested_wrapper_pattern = re.compile(r'(?:Promise<Result|Result<Promise|Option<Option|Result<Option|Option<Result)')
    void_pattern = re.compile(r'\bvoid\b')
    unit_import = 'org.pragmatica.lang.Unit' in content or 'import static org.pragmatica.lang.Unit' in content
    
    for i, line in enumerate(lines, 1):
        if nested_wrapper_pattern.search(line):
            issues.append(JBCTRuleIssue(
                rule='JBCT-RET-02',
                severity='error',
                category='return-types',
                line=i,
                message="Nested wrapper detected - simplify to single wrapper type",
                suggestion="Use either Promise<T> or Result<T>, not Promise<Result<T>>"
            ))
        
        if void_pattern.search(line) and 'return' not in line.lower():
            if not unit_import:
                issues.append(JBCTRuleIssue(
                    rule='JBCT-RET-04',
                    severity='warning',
                    category='return-types',
                    line=i,
                    message="Use Unit instead of Void for methods that return nothing",
                    suggestion="Import org.pragmatica.lang.Unit and return Unit.INSTANCE"
                ))
    
    return_result_pattern = re.compile(r'Result\<\w+\>\s+\w+\s*=.*Result\.success\(')
    if return_result_pattern.search(content):
        issues.append(JBCTRuleIssue(
            rule='JBCT-RET-05',
            severity='warning',
            category='return-types',
            line=1,
            message="Always-succeeding Result - return T directly instead",
            suggestion="If Result always succeeds, return T directly instead of Result<T>"
        ))
    
    return issues


def check_exception_rules_2(content: str, lines: List[str], config: Dict) -> List[JBCTRuleIssue]:
    """JBCT-EX-02: Don't use orElseThrow() - use Result/Option."""
    issues = []
    
    or_else_throw_pattern = re.compile(r'\.(?:orElseThrow|getOrThrow)\s*\(')
    
    for i, line in enumerate(lines, 1):
        if or_else_throw_pattern.search(line):
            issues.append(JBCTRuleIssue(
                rule='JBCT-EX-02',
                severity='error',
                category='exceptions',
                line=i,
                message="Use Result/Option for error handling, not orElseThrow()",
                suggestion="Handle Result/Option explicitly with onFailure() or recover()"
            ))
    
    return issues


def check_lambda_rules_2(content: str, lines: List[str], config: Dict) -> List[JBCTRuleIssue]:
    """JBCT-LAM-03: No ternary in lambdas - use filter() or extract.
       JBCT-NEST-01: No nested monadic operations in lambdas."""
    issues = []
    
    lambda_with_ternary = re.compile(r'(\w+)\s*->\s*[^}]*\?[^:]*:[^}]*\}')
    nested_monadic = re.compile(r'(\w+)\s*->\s*[^}]*\.(?:flatMap|map|filter)\s*\([^)]*\.(?:flatMap|map|filter)')
    
    for i, line in enumerate(lines, 1):
        if lambda_with_ternary.search(line):
            issues.append(JBCTRuleIssue(
                rule='JBCT-LAM-03',
                severity='warning',
                category='lambda',
                line=i,
                message="Ternary operator in lambda - use filter() or extract to method",
                suggestion="Replace ternary with .filter() or extract logic to named method"
            ))
        
        if nested_monadic.search(line):
            issues.append(JBCTRuleIssue(
                rule='JBCT-NEST-01',
                severity='warning',
                category='lambda',
                line=i,
                message="Nested monadic operations in lambda - extract to separate statements",
                suggestion="Use .flatMap() chains instead of nested operations"
            ))
    
    return issues


def check_patterns_2(content: str, lines: List[str], config: Dict) -> List[JBCTRuleIssue]:
    """JBCT-PAT-02: No Fork-Join inside Sequencer (Result.all inside flatMap).
       JBCT-SEQ-01: Chain length limit (2-5 steps)."""
    issues = []
    
    fork_in_sequencer = re.compile(r'flatMap\s*\([^)]*Result\.all\(')
    long_chain = re.compile(r'(\.(?:flatMap|map)\s*\([^)]+\)){6,}')
    
    for i, line in enumerate(lines, 1):
        if fork_in_sequencer.search(line):
            issues.append(JBCTRuleIssue(
                rule='JBCT-PAT-02',
                severity='warning',
                category='patterns',
                line=i,
                message="Fork-Join (Result.all) inside Sequencer (flatMap) - split into parallel steps",
                suggestion="Move Result.all() calls outside of flatMap chains"
            ))
        
        if long_chain.search(line):
            issues.append(JBCTRuleIssue(
                rule='JBCT-SEQ-01',
                severity='warning',
                category='patterns',
                line=i,
                message="Sequencer chain exceeds 5 steps - refactor into smaller methods",
                suggestion="Break long chains into separate methods (2-5 steps recommended)"
            ))
    
    return issues


def check_style_rules(content: str, lines: List[str], config: Dict) -> List[JBCTRuleIssue]:
    """JBCT-STY-01 to STY-06: Style rules."""
    issues = []
    
    failure_creation = re.compile(r'Result\.failure\(|Promise\.failure\(')
    constructor_ref = re.compile(r'v\s*->\s+new\s+\w+\s*\(\s*v\s*\)')
    qualified_name = re.compile(r'\b(?:org\.|com\.|io\.)[\w.]+\.\w+')
    utility_class = re.compile(r'class\s+\w*[Uu]tility\w*')
    method_ref = re.compile(r'(\w+)\s*->\s+\1\([^)]*\)')
    
    import_groups = {
        'java': 0,
        'javax': 0,
        'pragmatica': 0,
        'third_party': 0,
        'project': 0
    }
    
    for i, line in enumerate(lines, 1):
        if failure_creation.search(line):
            issues.append(JBCTRuleIssue(
                rule='JBCT-STY-01',
                severity='warning',
                category='style',
                line=i,
                message="Use cause.result() instead of Result.failure(cause)",
                suggestion="Use fluent failure: cause.result() not Result.failure(cause)"
            ))
        
        if constructor_ref.search(line):
            issues.append(JBCTRuleIssue(
                rule='JBCT-STY-02',
                severity='warning',
                category='style',
                line=i,
                message="Use constructor reference X::new instead of v -> new X(v)",
                suggestion="Replace lambda with method reference"
            ))
        
        if qualified_name.search(line) and 'import' not in line and 'package' not in line:
            issues.append(JBCTRuleIssue(
                rule='JBCT-STY-03',
                severity='warning',
                category='style',
                line=i,
                message="Use import instead of fully qualified class name",
                suggestion="Add import statement and use simple class name"
            ))
        
        if utility_class.search(line):
            if 'sealed' not in line and 'interface' not in line:
                issues.append(JBCTRuleIssue(
                    rule='JBCT-STY-04',
                    severity='warning',
                    category='style',
                    line=i,
                    message="Utility class should use sealed interface pattern",
                    suggestion="Use: sealed interface Utility permits Utility.Unused { record Unused() {} }"
                ))
        
        if method_ref.search(line):
            issues.append(JBCTRuleIssue(
                rule='JBCT-STY-05',
                severity='warning',
                category='style',
                line=i,
                message="Use method reference instead of equivalent lambda",
                suggestion="Replace v -> method(v) with this::method or Class::method"
            ))
    
    return issues


def check_import_order(content: str, lines: List[str], config: Dict) -> List[JBCTRuleIssue]:
    """JBCT-STY-06: Import ordering - java → javax → pragmatica → third-party → project."""
    issues = []
    
    import_pattern = re.compile(r'import\s+(static\s+)?([\w.]+)\.\w+;')
    imports = []
    for i, line in enumerate(lines, 1):
        match = import_pattern.search(line)
        if match:
            is_static = match.group(1) is not None
            pkg = match.group(2)
            imports.append((i, is_static, pkg))
    
    order_weights = {
        'java': 1, 'javax': 2,
        'org.pragmatica': 3,
        'com': 4, 'io': 4, 'net': 4,
    }
    
    for j in range(len(imports) - 1):
        curr_line, curr_static, curr_pkg = imports[j]
        next_line, next_static, next_pkg = imports[j + 1]
        
        if curr_static != next_static:
            continue
        
        curr_order = order_weights.get(curr_pkg.split('.')[0], 5)
        next_order = order_weights.get(next_pkg.split('.')[0], 5)
        
        if curr_order > next_order:
            issues.append(JBCTRuleIssue(
                rule='JBCT-STY-06',
                severity='warning',
                category='style',
                line=next_line,
                message=f"Import order: {next_pkg} should come before {curr_pkg}",
                suggestion="Order: java → javax → pragmatica → third-party → project"
            ))
            break
    
    return issues


def check_logging_rules(content: str, lines: List[str], config: Dict) -> List[JBCTRuleIssue]:
    """JBCT-LOG-01: No conditional logging - let log level handle filtering.
       JBCT-LOG-02: No logger as method parameter - component owns its logger."""
    issues = []
    
    conditional_log = re.compile(r'if\s*\([^)]*logger\.[a-z]+\([^)]+\)')
    logger_param = re.compile(r'\b\w+\s+logger\s*[,)]')
    
    for i, line in enumerate(lines, 1):
        if conditional_log.search(line):
            issues.append(JBCTRuleIssue(
                rule='JBCT-LOG-01',
                severity='warning',
                category='logging',
                line=i,
                message="Conditional logging - let log level handle filtering",
                suggestion="Remove if-check and use logger.debug/info/error directly"
            ))
        
        if logger_param.search(line):
            issues.append(JBCTRuleIssue(
                rule='JBCT-LOG-02',
                severity='warning',
                category='logging',
                line=i,
                message="Logger as method parameter - component should own its logger",
                suggestion="Use private final Logger logger = LoggerFactory.getLogger(getClass())"
            ))
    
    return issues


def check_static_imports(content: str, lines: List[str], config: Dict) -> List[JBCTRuleIssue]:
    """JBCT-STATIC-01: Prefer static imports for Pragmatica factories."""
    issues = []
    
    pragmatica_static = re.compile(r'(Result|Option|Promise)\.(success|failure|ok|err|some|none|promise)\(')
    static_import = re.compile(r'import\s+static\s+org\.pragmatica\.lang\.(Result|Option|Promise)\.')
    
    has_pragmatica = 'org.pragmatica' in content
    has_static_import = static_import.search(content) is not None
    
    if has_pragmatica and not has_static_import:
        issues.append(JBCTRuleIssue(
            rule='JBCT-STATIC-01',
            severity='warning',
            category='static-imports',
            line=1,
            message="Prefer static imports for Pragmatica factories",
            suggestion="Use: import static org.pragmatica.lang.Result.success;"
        ))
    
    return issues


def check_utilities(content: str, lines: List[str], config: Dict) -> List[JBCTRuleIssue]:
    """JBCT-UTIL-01: Use Pragmatica parsing utilities (Number.parseInt, etc).
       JBCT-UTIL-02: Use Verify.Is predicates for validation."""
    issues = []
    
    parse_int = re.compile(r'Integer\.parseInt\(|Long\.parseLong\(')
    verify_import = 'org.pragmatica.lang.Verify' in content
    
    for i, line in enumerate(lines, 1):
        if parse_int.search(line):
            issues.append(JBCTRuleIssue(
                rule='JBCT-UTIL-01',
                severity='warning',
                category='utilities',
                line=i,
                message="Use Pragmatica parsing utilities instead of JDK",
                suggestion="Use Number.parseInt() or Number.parseLong() from org.pragmatica.lang.parse"
            ))
        
        if 'if (' in line or 'assert ' in line:
            if not verify_import and any(kw in line.lower() for kw in ['null', 'empty', 'blank', 'positive']):
                issues.append(JBCTRuleIssue(
                    rule='JBCT-UTIL-02',
                    severity='warning',
                    category='utilities',
                    line=i,
                    message="Use Verify.Is predicates for validation",
                    suggestion="Use Verify.Is.notNull, Verify.Is::lenBetween, etc."
                ))
    
    return issues


def check_acronyms(content: str, lines: List[str], config: Dict) -> List[JBCTRuleIssue]:
    """JBCT-ACR-01: Acronyms should use PascalCase (HttpClient, not HTTPClient)."""
    issues = []
    
    acronym_pattern = re.compile(r'\b[A-Z]{2,}[a-z]|[a-z][A-Z]{2,}')
    
    common_acronyms = {'API', 'HTTP', 'URL', 'URI', 'ID', 'XML', 'JSON', 'SQL', 'JDBC', 'DTO', 'DAO'}
    
    for i, line in enumerate(lines, 1):
        if 'class ' in line or 'interface ' in line or 'record ' in line:
            for match in acronym_pattern.finditer(line):
                word = match.group()
                if any(ac in word.upper() for ac in common_acronyms):
                    issues.append(JBCTRuleIssue(
                        rule='JBCT-ACR-01',
                        severity='warning',
                        category='naming',
                        line=i,
                        message=f"Acronym '{word}' should use PascalCase",
                        suggestion="Use HttpClient not HTTPClient, Url not URL in class names"
                    ))
    
    return issues


def check_sealed_errors(content: str, lines: List[str], config: Dict) -> List[JBCTRuleIssue]:
    """JBCT-SEAL-01: Error interfaces extending Cause should be sealed."""
    issues = []
    
    error_interface = re.compile(r'interface\s+(\w+(?:Error|Exception|Cause))\s+extends\s+(?:Cause|.*Cause)')
    sealed_keyword = re.compile(r'sealed\s+interface')
    
    for match in error_interface.finditer(content):
        interface_name = match.group(1)
        start_pos = match.start()
        line_num = content[:start_pos].count('\n') + 1
        
        check_start = max(0, start_pos - 50)
        check_content = content[check_start:start_pos + 100]
        
        if 'sealed' not in check_content:
            issues.append(JBCTRuleIssue(
                rule='JBCT-SEAL-01',
                severity='warning',
                category='sealed-types',
                line=line_num,
                message=f"Error interface '{interface_name}' should be sealed",
                suggestion="Use: sealed interface ErrorName extends Cause permits ... { }"
            ))
    
    return issues


def check_usecase_pattern(content: str, lines: List[str], config: Dict) -> List[JBCTRuleIssue]:
    """JBCT-UC-01: Use case factories should return lambdas, not nested records."""
    issues = []
    
    factory_return_record = re.compile(r'static\s+\w+\s+\w+\s*\([^)]*\)\s*\{[^}]*return\s+new\s+\w+\(')
    
    if factory_return_record.search(content):
        issues.append(JBCTRuleIssue(
            rule='JBCT-UC-01',
            severity='warning',
            category='usecase',
            line=1,
            message="Use case factory returns record - return lambda instead",
            suggestion="Return: req -> new UseCaseImpl(req) instead of new UseCase(req)"
        ))
    
    return issues


def run_jbct_analysis(file_path: str, config: Dict, package: str = "") -> Dict:
    """Run JBCT compliance analysis on a Java file."""
    result = {
        'file_path': file_path,
        'package': package,
        'issues': [],
        'summary': {'errors': 0, 'warnings': 0}
    }
    
    if not os.path.exists(file_path):
        result['error'] = f'File not found: {file_path}'
        return result
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    jbct_profile = config.get('jbct_profile', 'disabled')
    if jbct_profile == 'disabled':
        return result
    
    jbct_rules = config.get('jbct_rules', {})
    
    all_issues = []
    
    if jbct_rules.get('return_types', True):
        all_issues.extend(check_return_types(content, lines, config))
        all_issues.extend(check_return_types_2(content, lines, config))
    
    if jbct_rules.get('exceptions', True):
        all_issues.extend(check_exceptions(content, lines, config))
        all_issues.extend(check_exception_rules_2(content, lines, config))
    
    if jbct_rules.get('value_objects', True):
        all_issues.extend(check_value_objects(content, lines, config))
    
    if jbct_rules.get('lambda_rules', True):
        all_issues.extend(check_lambda_rules(content, lines, config))
        all_issues.extend(check_lambda_rules_2(content, lines, config))
    
    if jbct_rules.get('patterns', True):
        all_issues.extend(check_patterns(content, lines, config))
        all_issues.extend(check_patterns_2(content, lines, config))
    
    if jbct_rules.get('architecture', True):
        all_issues.extend(check_architecture(content, lines, config, package))
    
    if jbct_rules.get('naming', True):
        all_issues.extend(check_naming(content, lines, config))
        all_issues.extend(check_acronyms(content, lines, config))
    
    if jbct_rules.get('zones', True):
        all_issues.extend(check_zones(content, lines, config, package))
    
    if jbct_rules.get('style', True):
        all_issues.extend(check_style_rules(content, lines, config))
        all_issues.extend(check_import_order(content, lines, config))
    
    if jbct_rules.get('logging', True):
        all_issues.extend(check_logging_rules(content, lines, config))
    
    if jbct_rules.get('static_imports', True):
        all_issues.extend(check_static_imports(content, lines, config))
    
    if jbct_rules.get('utilities', True):
        all_issues.extend(check_utilities(content, lines, config))
    
    if jbct_rules.get('sealed_types', True):
        all_issues.extend(check_sealed_errors(content, lines, config))
    
    if jbct_rules.get('usecase', True):
        all_issues.extend(check_usecase_pattern(content, lines, config))
    
    for issue in all_issues:
        result['issues'].append({
            'rule': issue.rule,
            'severity': issue.severity,
            'category': issue.category,
            'line': issue.line,
            'message': issue.message,
            'suggestion': issue.suggestion
        })
        
        if issue.severity == 'error':
            result['summary']['errors'] += 1
        else:
            result['summary']['warnings'] += 1
    
    return result


async def analyze_jbct(file_path: str, config: Dict) -> Dict:
    """Async wrapper for JBCT analysis."""
    return run_jbct_analysis(file_path, config)

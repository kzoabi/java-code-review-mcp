"""Spring Boot / Spring Framework Analyzer Module"""
import re
import os
from typing import Dict, List
from dataclasses import dataclass
from typing import Optional


@dataclass
class SpringIssue:
    rule: str
    severity: str
    category: str
    line: int
    message: str
    suggestion: Optional[str] = None


# ---------------------------------------------------------------------------
# Rule: @Transactional on non-public methods (ignored by Spring proxy)
# ---------------------------------------------------------------------------
_TRANSACTIONAL_METHOD = re.compile(
    r'@Transactional[^\n]*\n\s*(?:(?:@\w+[^\n]*\n\s*)*)?'
    r'(private|protected|package|default)\s',
    re.MULTILINE,
)
_TRANSACTIONAL_PRIVATE = re.compile(
    r'@Transactional', re.MULTILINE
)


def check_transactional(content: str, lines: List[str]) -> List[SpringIssue]:
    issues = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if '@Transactional' not in stripped:
            continue
        # Look ahead to find the method visibility
        for j in range(i, min(i + 5, len(lines))):
            ahead = lines[j].strip()
            if not ahead or ahead.startswith('@') or ahead.startswith('//'):
                continue
            if re.search(r'\b(private|protected)\b', ahead):
                vis = 'private' if 'private' in ahead else 'protected'
                issues.append(SpringIssue(
                    rule='SPRING-TX-01',
                    severity='major',
                    category='spring-transactional',
                    line=i,
                    message=f"@Transactional on {vis} method — Spring proxy cannot intercept it",
                    suggestion="Make the method public or use AspectJ mode (proxyTargetClass is not enough)"
                ))
            break
    return issues


# ---------------------------------------------------------------------------
# Rule: Field injection via @Autowired (prefer constructor injection)
# ---------------------------------------------------------------------------
_FIELD_AUTOWIRED = re.compile(
    r'@Autowired\s*\n\s*(?:private|protected|public)\s+(?!static)(\w+)\s+(\w+)\s*;',
    re.MULTILINE,
)


def check_field_injection(content: str, lines: List[str]) -> List[SpringIssue]:
    issues = []
    for m in _FIELD_AUTOWIRED.finditer(content):
        line_num = content[:m.start()].count('\n') + 1
        field_type = m.group(1)
        field_name = m.group(2)
        issues.append(SpringIssue(
            rule='SPRING-DI-01',
            severity='major',
            category='spring-injection',
            line=line_num,
            message=f"Field injection @Autowired {field_type} {field_name} — prefer constructor injection",
            suggestion="Add a constructor parameter and mark it with @Autowired (or use Lombok @RequiredArgsConstructor)"
        ))
    return issues


# ---------------------------------------------------------------------------
# Rule: Missing stereotype annotations (@Service / @Repository / @Component)
# ---------------------------------------------------------------------------
_CLASS_DEF = re.compile(r'(?:public\s+)?(?:final\s+)?class\s+(\w+)')
_STEREOTYPE_PATTERN = re.compile(
    r'@(?:Service|Repository|Component|Controller|RestController|Configuration)'
)
_IMPLEMENTS_PATTERN = re.compile(r'implements\s+([\w,\s]+)')


def check_missing_stereotype(content: str, lines: List[str]) -> List[SpringIssue]:
    issues = []
    # Only flag if project uses Spring (has at least one stereotype somewhere)
    if not _STEREOTYPE_PATTERN.search(content):
        return issues

    for i, line in enumerate(lines, 1):
        m = _CLASS_DEF.search(line)
        if not m:
            continue
        class_name = m.group(1)
        # Skip abstract, interface, enum, test classes, records
        if any(kw in line for kw in ('abstract', 'interface', 'enum', '@', 'record')):
            continue
        if class_name.endswith('Test') or class_name.endswith('Tests'):
            continue
        # Check 5 lines above for any stereotype annotation
        start = max(0, i - 6)
        context = '\n'.join(lines[start:i])
        if _STEREOTYPE_PATTERN.search(context):
            continue
        # Only flag classes that implement a service-like interface
        impl_match = _IMPLEMENTS_PATTERN.search(line)
        if impl_match:
            interfaces = impl_match.group(1)
            if any(kw in interfaces for kw in ('Service', 'Repository', 'UseCase', 'Port')):
                issues.append(SpringIssue(
                    rule='SPRING-STEREO-01',
                    severity='minor',
                    category='spring-stereotype',
                    line=i,
                    message=f"Class '{class_name}' implements a service interface but has no Spring stereotype",
                    suggestion="Add @Service, @Repository, or @Component to register as a Spring bean"
                ))
    return issues


# ---------------------------------------------------------------------------
# Rule: @RestController methods returning raw types instead of ResponseEntity
# ---------------------------------------------------------------------------
_REST_CONTROLLER = re.compile(r'@RestController')
_RAW_RETURN_METHOD = re.compile(
    r'(?:@(?:GetMapping|PostMapping|PutMapping|DeleteMapping|RequestMapping)[^\n]*\n\s*)'
    r'public\s+(?!ResponseEntity|Mono|Flux|CompletableFuture|void)(\w+)\s+(\w+)\s*\(',
    re.MULTILINE,
)


def check_rest_controller_return_types(content: str, lines: List[str]) -> List[SpringIssue]:
    issues = []
    if not _REST_CONTROLLER.search(content):
        return issues
    for m in _RAW_RETURN_METHOD.finditer(content):
        return_type = m.group(1)
        method_name = m.group(2)
        line_num = content[:m.start()].count('\n') + 1
        issues.append(SpringIssue(
            rule='SPRING-REST-01',
            severity='minor',
            category='spring-rest',
            line=line_num,
            message=f"@RestController method '{method_name}' returns raw {return_type} — consider ResponseEntity",
            suggestion=f"Return ResponseEntity<{return_type}> for full HTTP control (status, headers)"
        ))
    return issues


# ---------------------------------------------------------------------------
# Rule: @Value with hardcoded fallback that masks missing config
# ---------------------------------------------------------------------------
_VALUE_HARDCODED = re.compile(
    r'@Value\s*\(\s*"\$\{[^}]+:[^}]+\}"\s*\)',
    re.MULTILINE,
)


def check_value_hardcoded_fallback(content: str, lines: List[str]) -> List[SpringIssue]:
    issues = []
    for m in _VALUE_HARDCODED.finditer(content):
        line_num = content[:m.start()].count('\n') + 1
        issues.append(SpringIssue(
            rule='SPRING-CONFIG-01',
            severity='minor',
            category='spring-config',
            line=line_num,
            message="@Value with hardcoded fallback may mask missing configuration property",
            suggestion="Remove the default value or use @ConfigurationProperties for type-safe config binding"
        ))
    return issues


# ---------------------------------------------------------------------------
# Rule: Circular @Autowired dependency (simple: class A injects class B which injects class A)
# ---------------------------------------------------------------------------
def check_circular_autowired(content: str, lines: List[str], class_names_in_project: List[str]) -> List[SpringIssue]:
    """Flag if a class injects itself (trivial cycle) or has suspicious self-reference."""
    issues = []
    # Extract this class name
    class_match = _CLASS_DEF.search(content)
    if not class_match:
        return issues
    this_class = class_match.group(1)
    # Check if this class has @Autowired / constructor param that injects itself
    inject_pattern = re.compile(r'(?:@Autowired|@Inject)[^\n]*\n\s*(?:private|protected|public)?\s+' + re.escape(this_class) + r'\s+\w+')
    if inject_pattern.search(content):
        issues.append(SpringIssue(
            rule='SPRING-DI-02',
            severity='major',
            category='spring-injection',
            line=1,
            message=f"Class '{this_class}' appears to inject itself — circular dependency",
            suggestion="Refactor to break the circular dependency; use @Lazy as a last resort"
        ))
    return issues


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def run_spring_analysis(file_path: str, config: Dict,
                         class_names_in_project: Optional[List[str]] = None) -> Dict:
    """Run Spring Boot compliance analysis on a Java file."""
    result: Dict = {
        'file_path': file_path,
        'issues': [],
        'summary': {'errors': 0, 'warnings': 0}
    }

    if not os.path.exists(file_path):
        result['error'] = f'File not found: {file_path}'
        return result

    spring_rules = config.get('spring_rules', {})
    if not config.get('spring_enabled', True):
        return result

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    lines = content.split('\n')

    all_issues: List[SpringIssue] = []

    if spring_rules.get('transactional', True):
        all_issues.extend(check_transactional(content, lines))

    if spring_rules.get('field_injection', True):
        all_issues.extend(check_field_injection(content, lines))

    if spring_rules.get('missing_stereotype', True):
        all_issues.extend(check_missing_stereotype(content, lines))

    if spring_rules.get('rest_return_types', True):
        all_issues.extend(check_rest_controller_return_types(content, lines))

    if spring_rules.get('value_fallback', True):
        all_issues.extend(check_value_hardcoded_fallback(content, lines))

    if spring_rules.get('circular_autowired', True):
        all_issues.extend(check_circular_autowired(content, lines, class_names_in_project or []))

    for issue in all_issues:
        result['issues'].append({
            'rule': issue.rule,
            'severity': issue.severity,
            'category': issue.category,
            'line': issue.line,
            'message': issue.message,
            'suggestion': issue.suggestion,
        })
        if issue.severity in ('critical', 'major'):
            result['summary']['errors'] += 1
        else:
            result['summary']['warnings'] += 1

    return result

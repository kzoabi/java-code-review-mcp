"""Report Generator Module - Markdown/JSON/SARIF output"""
import json
from datetime import datetime
from typing import Dict, Any, List

SEVERITY_MAP = {
    'critical': 'error',
    'major': 'warning',
    'minor': 'note'
}

def generate_report(result: Dict, output_format: str = 'markdown') -> str:
    """Generate a code review report in the specified format."""
    if output_format == 'json':
        return json.dumps(result, indent=2, default=str)
    elif output_format == 'sarif':
        return generate_sarif_report(result)
    elif output_format == 'both':
        md = generate_markdown(result)
        json_str = json.dumps(result, indent=2, default=str)
        return f"{md}\n\n---\n\n## JSON Output\n\n```json\n{json_str}\n```"
    else:
        return generate_markdown(result)


def generate_sarif_report(result: Dict) -> str:
    """Generate a SARIF 2.1.0 report for code review results."""
    runs = []
    
    run = {
        "tool": {
            "driver": {
                "name": "Java Code Review MCP",
                "version": "1.0.0",
                "informationUri": "https://github.com/java-code-review-mcp",
                "rules": []
            }
        },
        "results": []
    }
    
    rules_map = {}
    results_list = []
    rule_id = 1
    
    issues = result.get('issues', [])
    for issue in issues:
        severity = issue.get('severity', 'minor')
        category = issue.get('category', 'unknown')
        message = issue.get('message', 'No message')
        line = issue.get('line', 1)
        rule = issue.get('rule', f'JCR-{category.upper()}-{rule_id}')
        
        rule_key = rule
        if rule_key not in rules_map:
            rules_map[rule_key] = {
                "id": rule_key,
                "name": category.title(),
                "shortDescription": {
                    "text": message[:100]
                },
                "helpUri": f"https://github.com/java-code-review-mcp/rules#{rule_key.lower()}"
            }
            run["tool"]["driver"]["rules"].append(rules_map[rule_key])
        
        result_entry = {
            "ruleId": rule_key,
            "level": SEVERITY_MAP.get(severity, 'note'),
            "message": {
                "text": message
            },
            "locations": []
        }
        
        file_path = result.get('file_path', result.get('project_path', 'unknown'))
        if file_path:
            result_entry["locations"].append({
                "physicalLocation": {
                    "artifactLocation": {
                        "uri": file_path.replace('\\', '/'),
                        "uriBaseId": "SRCROOT"
                    },
                    "region": {
                        "startLine": line,
                        "startColumn": 1
                    }
                }
            })
        
        results_list.append(result_entry)
        rule_id += 1
    
    run["results"] = results_list
    
    if not run["tool"]["driver"]["rules"]:
        run["tool"]["driver"]["rules"].append({
            "id": "JCR-001",
            "name": "General",
            "shortDescription": {"text": "Code review issue"}
        })
    
    runs.append(run)
    
    sarif_output = {
        "version": "2.1.0",
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "runs": runs
    }
    
    return json.dumps(sarif_output, indent=2)

def generate_markdown(result: Dict) -> str:
    """Generate a markdown code review report."""
    md = "# Java Code Review Report\n\n"
    if 'file_path' in result:
        md += f"**File:** `{result['file_path']}`\n\n"
    if 'project_path' in result:
        md += f"**Project:** `{result['project_path']}`\n\n"
    if 'repo_path' in result:
        md += f"**Repository:** `{result['repo_path']}`\n\n"
    if 'review_level' in result:
        md += f"**Review Level:** {result['review_level']}\n\n"
    md += "---\n\n"
    if 'summary' in result:
        md += "## Summary\n\n"
        summary = result['summary']
        md += f"- **Files Reviewed:** {summary.get('total_files', 'N/A')}\n"
        md += f"- **Total Issues:** {summary.get('total_issues', 0)}\n"
        md += f"  - Critical: {summary.get('critical', 0)}\n"
        md += f"  - Major: {summary.get('major', 0)}\n"
        md += f"  - Minor: {summary.get('minor', 0)}\n"
        md += "\n"
    if 'issues' in result and result['issues']:
## Issues Found\n        md += "\n"
        by_severity = {'critical': [], 'major': [], 'minor': []}
        for issue in result['issues']:
            severity = issue.get('severity', 'minor')
            if severity in by_severity:
                by_severity[severity].append(issue)
        for severity in ['critical', 'major', 'minor']:
            if by_severity[severity]:
                md += f"### {severity.upper()}\n\n"
                for issue in by_severity[severity]:
                    line = issue.get('line', '?')
                    category = issue.get('category', 'unknown')
                    message = issue.get('message', 'No message')
                    rule = issue.get('rule', '')
                    md += f"- **Line {line}** [{category}] {message}"
                    if rule:
                        md += f" (`{rule}`)"
                    md += "\n"
                md += "\n"
    if 'suggestions' in result and result['suggestions']:
        md += "## Suggestions (JDK 17+)\n\n"
        for suggestion in result['suggestions']:
            line = suggestion.get('line', '?')
            message = suggestion.get('message', '')
            details = suggestion.get('suggestion', '')
            md += f"- **Line {line}:** {message}"
            if details:
                md += f" - {details}"
            md += "\n"
        md += "\n"
    if 'dependencies' in result and result.get('dependencies'):
        md += "## Dependencies\n\n"
        deps = result['dependencies']
        if 'dependencies' in deps:
            md += f"**Build Tool:** {deps.get('build_tool', 'unknown')}\n\n"
            md += f"**Total Dependencies:** {len(deps.get('dependencies', []))}\n\n"
            if deps.get('issues'):
                md += "### Issues\n\n"
                for issue in deps['issues']:
                    md += f"- {issue.get('issue', '')}: {issue.get('dependency', '')}\n"
        md += "\n"
    if 'metrics' in result:
        md += "## Metrics\n\n"
        metrics = result['metrics']
        md += f"- **Total Lines:** {metrics.get('total_lines', 0)}\n"
        md += f"- **Code Lines:** {metrics.get('code_lines', 0)}\n"
        md += f"- **Comment Lines:** {metrics.get('comment_lines', 0)}\n"
        md += f"- **Blank Lines:** {metrics.get('blank_lines', 0)}\n"
        md += "\n"
    if 'classes' in result:
        md += "## Classes\n\n"
        for cls in result['classes']:
            md += f"### {cls.get('name', 'Unknown')}\n\n"
            md += f"- **Type:** {'Record' if cls.get('is_record') else 'Class'}\n"
            if cls.get('extends'):
                md += f"- **Extends:** {cls['extends']}\n"
            if cls.get('implements'):
                md += f"- **Implements:** {', '.join(cls['implements'])}\n"
            md += f"- **Fields:** {cls.get('fields_count', 0)}\n"
            md += f"- **Methods:** {cls.get('methods_count', 0)}\n"
            md += f"- **Lines:** {cls.get('lines', 0)}\n"
            md += "\n"
    if 'error' in result:
        md += f"**Error:** {result['error']}\n"
    
    if 'jbct_issues' in result and result.get('jbct_issues'):
        md += "## JBCT Methodology Issues\n\n"
        jbct_issues = result['jbct_issues']
        by_severity = {'error': [], 'warning': []}
        for issue in jbct_issues:
            severity = issue.get('severity', 'warning')
            if severity in by_severity:
                by_severity[severity].append(issue)
        
        if by_severity['error']:
            md += "### Errors\n\n"
            for issue in by_severity['error']:
                line = issue.get('line', '?')
                rule = issue.get('rule', '')
                message = issue.get('message', '')
                suggestion = issue.get('suggestion', '')
                md += f"- **Line {line}** `{rule}` {message}"
                if suggestion:
                    md += f"\n  - Suggestion: {suggestion}"
                md += "\n"
            md += "\n"
        
        if by_severity['warning']:
            md += "### Warnings\n\n"
            for issue in by_severity['warning']:
                line = issue.get('line', '?')
                rule = issue.get('rule', '')
                message = issue.get('message', '')
                suggestion = issue.get('suggestion', '')
                md += f"- **Line {line}** `{rule}` {message}"
                if suggestion:
                    md += f"\n  - Suggestion: {suggestion}"
                md += "\n"
            md += "\n"
    
    if 'jbct_profile' in result:
        md += f"**JBCT Profile:** {result['jbct_profile']}\n\n"
    
    if 'package_structure' in result:
        md += "## Architecture\n\n"
        structure = result['package_structure']
        md += "### Package Structure\n\n"
        for layer, exists in structure.items():
            status = "✓" if exists else "✗"
            md += f"- {status} {layer.capitalize()}: {'Found' if exists else 'Not found'}\n"
        md += "\n"
    
    if 'circular_dependencies' in result and result.get('circular_dependencies'):
        md += "### Circular Dependencies\n\n"
        for dep in result['circular_dependencies']:
            md += f"- {dep.get('message', 'Unknown')}\n"
        md += "\n"
    
    if 'import_flow_issues' in result and result.get('import_flow_issues'):
        md += "### Import Flow Issues\n\n"
        for issue in result['import_flow_issues']:
            md += f"- Domain → Adapter: {issue.get('from_package', '?')} → {issue.get('to_package', '?')}\n"
        md += "\n"
    
    if 'summary' in result and 'errors' in result['summary']:
        summary = result['summary']
        md += f"**Total Errors:** {summary.get('errors', 0)}\n"
        md += f"**Total Warnings:** {summary.get('warnings', 0)}\n"
    
    return md

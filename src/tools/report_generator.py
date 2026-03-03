"""Report Generator Module - Markdown/JSON/SARIF output"""
import json
from collections import defaultdict
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


# ---------------------------------------------------------------------------
# SARIF
# ---------------------------------------------------------------------------
def generate_sarif_report(result: Dict) -> str:
    """Generate a SARIF 2.1.0 report for code review results."""
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
                "shortDescription": {"text": message[:100]},
                "helpUri": f"https://github.com/java-code-review-mcp/rules#{rule_key.lower()}"
            }
            run["tool"]["driver"]["rules"].append(rules_map[rule_key])

        result_entry = {
            "ruleId": rule_key,
            "level": SEVERITY_MAP.get(severity, 'note'),
            "message": {"text": message},
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
                    "region": {"startLine": line, "startColumn": 1}
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

    sarif_output = {
        "version": "2.1.0",
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "runs": [run]
    }

    return json.dumps(sarif_output, indent=2)


# ---------------------------------------------------------------------------
# Markdown helpers
# ---------------------------------------------------------------------------
def _anchor(text: str) -> str:
    """GitHub-flavoured markdown anchor from heading text."""
    return '#' + re.sub(r'[^a-z0-9-]', '', text.lower().replace(' ', '-'))


import re


def _severity_emoji(severity: str) -> str:
    return {'critical': '🔴', 'major': '🟠', 'minor': '🟡',
            'error': '🔴', 'warning': '🟠', 'note': '🟡'}.get(severity, '⚪')


def _issues_by_file(issues: List[Dict]) -> Dict[str, List[Dict]]:
    grouped: Dict[str, List[Dict]] = defaultdict(list)
    for issue in issues:
        fp = issue.get('file_path', issue.get('file', 'unknown'))
        grouped[fp].append(issue)
    return dict(grouped)


def _top_files(issues: List[Dict], n: int = 5) -> List[tuple]:
    counts: Dict[str, int] = defaultdict(int)
    for issue in issues:
        fp = issue.get('file_path', issue.get('file', 'unknown'))
        counts[fp] += 1
    return sorted(counts.items(), key=lambda x: x[1], reverse=True)[:n]


# ---------------------------------------------------------------------------
# Main Markdown generator
# ---------------------------------------------------------------------------
def generate_markdown(result: Dict) -> str:
    sections = []          # list of (heading, anchor_id, content) tuples
    toc_entries = []       # list of (level, label, anchor)

    md_header = "# Java Code Review Report\n\n"
    if 'file_path' in result:
        md_header += f"**File:** `{result['file_path']}`\n\n"
    if 'project_path' in result:
        md_header += f"**Project:** `{result['project_path']}`\n\n"
    if 'repo_path' in result:
        md_header += f"**Repository:** `{result['repo_path']}`\n\n"
    if 'review_level' in result:
        md_header += f"**Review Level:** {result['review_level']}\n\n"
    md_header += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n---\n\n"

    # -----------------------------------------------------------------------
    # Summary dashboard
    # -----------------------------------------------------------------------
    summary_md = ""
    summary = result.get('summary', {})
    issues = result.get('issues', [])
    jbct_issues = result.get('jbct_issues', [])
    arch_issues = result.get('architecture_issues', [])
    spring_issues = [i for i in issues if i.get('category', '').startswith('spring')]

    total_issues = len(issues) + len(jbct_issues) + len(arch_issues)
    critical_count = sum(1 for i in issues if i.get('severity') == 'critical')
    major_count = sum(1 for i in issues if i.get('severity') == 'major')
    minor_count = sum(1 for i in issues if i.get('severity') == 'minor')

    summary_md += "| Metric | Value |\n|--------|-------|\n"
    if summary.get('total_files') is not None:
        summary_md += f"| Files Reviewed | {summary['total_files']} |\n"
    summary_md += f"| Total Issues | {total_issues} |\n"
    summary_md += f"| 🔴 Critical | {critical_count} |\n"
    summary_md += f"| 🟠 Major | {major_count} |\n"
    summary_md += f"| 🟡 Minor | {minor_count} |\n"
    if jbct_issues:
        jbct_errors = sum(1 for i in jbct_issues if i.get('severity') == 'error')
        jbct_warn = sum(1 for i in jbct_issues if i.get('severity') == 'warning')
        summary_md += f"| JBCT Errors | {jbct_errors} |\n"
        summary_md += f"| JBCT Warnings | {jbct_warn} |\n"
    if arch_issues:
        summary_md += f"| Architecture Issues | {len(arch_issues)} |\n"
    if result.get('version_conflicts') or (result.get('dependencies', {}) or {}).get('version_conflicts'):
        vc = result.get('version_conflicts', (result.get('dependencies') or {}).get('version_conflicts', []))
        summary_md += f"| Dependency Version Conflicts | {len(vc)} |\n"
    sections.append(("Summary", "summary", summary_md))
    toc_entries.append((2, "Summary", "summary"))

    # -----------------------------------------------------------------------
    # Top problematic files
    # -----------------------------------------------------------------------
    if issues and 'project_path' in result:
        top = _top_files(issues)
        if top:
            top_md = "| File | Issues |\n|------|--------|\n"
            for fp, cnt in top:
                import os
                short = fp.replace(result['project_path'], '').lstrip('/\\')
                top_md += f"| `{short}` | {cnt} |\n"
            sections.append(("Top Problematic Files", "top-problematic-files", top_md))
            toc_entries.append((2, "Top Problematic Files", "top-problematic-files"))

    # -----------------------------------------------------------------------
    # Issues section (by severity, then by file)
    # -----------------------------------------------------------------------
    if issues:
        by_severity: Dict[str, List[Dict]] = defaultdict(list)
        for issue in issues:
            by_severity[issue.get('severity', 'minor')].append(issue)

        issues_md = ""
        for sev in ['critical', 'major', 'minor']:
            if not by_severity[sev]:
                continue
            emoji = _severity_emoji(sev)
            sev_anchor = f"issues-{sev}"
            issues_md += f"### {emoji} {sev.upper()}\n\n"
            toc_entries.append((3, f"{emoji} {sev.upper()}", sev_anchor))

            # Group by file within severity
            by_file: Dict[str, List[Dict]] = defaultdict(list)
            for issue in by_severity[sev]:
                fp = issue.get('file_path', '')
                by_file[fp].append(issue)

            for fp, file_issues in sorted(by_file.items()):
                if fp:
                    import os
                    short = fp.replace(result.get('project_path', ''), '').lstrip('/\\')
                    issues_md += f"**`{short or fp}`**\n\n"
                for issue in file_issues:
                    line = issue.get('line', '?')
                    category = issue.get('category', 'unknown')
                    message = issue.get('message', 'No message')
                    rule = issue.get('rule', '')
                    issues_md += f"- **Line {line}** [{category}] {message}"
                    if rule:
                        issues_md += f" (`{rule}`)"
                    issues_md += "\n"
                issues_md += "\n"

        sections.append(("Issues Found", "issues-found", issues_md))
        toc_entries.append((2, "Issues Found", "issues-found"))

    # -----------------------------------------------------------------------
    # JBCT issues
    # -----------------------------------------------------------------------
    if jbct_issues:
        jbct_md = ""
        by_sev: Dict[str, List] = defaultdict(list)
        for issue in jbct_issues:
            by_sev[issue.get('severity', 'warning')].append(issue)

        for sev_label, sev_key in [('Errors', 'error'), ('Warnings', 'warning')]:
            if not by_sev[sev_key]:
                continue
            jbct_md += f"### {sev_label}\n\n"
            for issue in by_sev[sev_key]:
                line = issue.get('line', '?')
                rule = issue.get('rule', '')
                message = issue.get('message', '')
                suggestion = issue.get('suggestion', '')
                jbct_md += f"- **Line {line}** `{rule}` {message}"
                if suggestion:
                    jbct_md += f"\n  - *{suggestion}*"
                jbct_md += "\n"
            jbct_md += "\n"

        sections.append(("JBCT Methodology Issues", "jbct-methodology-issues", jbct_md))
        toc_entries.append((2, "JBCT Methodology Issues", "jbct-methodology-issues"))

    # -----------------------------------------------------------------------
    # Architecture analysis (F5 / F10)
    # -----------------------------------------------------------------------
    has_arch = (arch_issues or result.get('package_structure') or
                result.get('circular_dependencies') or result.get('import_flow_issues'))
    if has_arch:
        arch_md = ""

        # Package structure
        pkg_structure = result.get('package_structure', {})
        if pkg_structure:
            arch_md += "### Package Structure\n\n"
            toc_entries.append((3, "Package Structure", "package-structure"))
            for layer, exists in pkg_structure.items():
                status = "✓" if exists else "✗"
                arch_md += f"- {status} **{layer.capitalize()}**: {'Found' if exists else 'Not found'}\n"
            arch_md += "\n"

        # F10: Dependency matrix
        packages_info = result.get('packages', {})
        if packages_info:
            arch_md += _render_dependency_matrix(packages_info)
            toc_entries.append((3, "Layer Dependency Matrix", "layer-dependency-matrix"))

        # Circular dependencies
        circular = result.get('circular_dependencies', [])
        if circular:
            arch_md += "### Circular Dependencies\n\n"
            toc_entries.append((3, "Circular Dependencies", "circular-dependencies"))
            for dep in circular:
                arch_md += f"- {dep.get('message', 'Unknown')}\n"
            arch_md += "\n"

        # Import flow issues
        import_flow = result.get('import_flow_issues', [])
        if import_flow:
            arch_md += "### Import Flow Violations\n\n"
            toc_entries.append((3, "Import Flow Violations", "import-flow-violations"))
            for issue in import_flow:
                arch_md += f"- `{issue.get('from_package', '?')}` → `{issue.get('to_package', '?')}`\n"
            arch_md += "\n"

        # Other architecture issues
        if arch_issues:
            arch_md += "### Architecture Issues\n\n"
            toc_entries.append((3, "Architecture Issues", "architecture-issues"))
            for issue in arch_issues:
                sev = issue.get('severity', 'warning')
                emoji = _severity_emoji(sev)
                arch_md += f"- {emoji} {issue.get('message', '')}\n"
                if issue.get('suggestion'):
                    arch_md += f"  - *{issue['suggestion']}*\n"
            arch_md += "\n"

        sections.append(("Architecture Analysis", "architecture-analysis", arch_md))
        toc_entries.append((2, "Architecture Analysis", "architecture-analysis"))

    # -----------------------------------------------------------------------
    # Dependencies (multi-module aware)
    # -----------------------------------------------------------------------
    deps_data = result.get('dependencies', {})
    if deps_data and isinstance(deps_data, dict):
        dep_md = ""
        dep_md += f"**Build Tool:** {deps_data.get('build_tool', 'unknown')}\n\n"
        modules = deps_data.get('modules', [])
        if modules:
            dep_md += f"**Modules:** {len(modules)}\n\n"
            dep_md += "| Module | Dependencies |\n|--------|-------------|\n"
            for mod in modules:
                dep_md += f"| `{mod['name']}` | {mod['dependency_count']} |\n"
            dep_md += "\n"
        dep_md += f"**Total Dependencies:** {len(deps_data.get('dependencies', []))}\n\n"

        version_conflicts = deps_data.get('version_conflicts', [])
        if version_conflicts:
            dep_md += "### Version Conflicts\n\n"
            for vc in version_conflicts:
                dep_md += f"- **{vc['dependency']}**: {vc['issue']}\n"
                dep_md += f"  - Modules: {', '.join(vc.get('modules', []))}\n"
            dep_md += "\n"

        dep_issues = deps_data.get('issues', [])
        if dep_issues:
            dep_md += "### Dependency Issues\n\n"
            for issue in dep_issues:
                dep_md += f"- {issue.get('issue', issue.get('error', ''))}: `{issue.get('dependency', issue.get('file', ''))}`\n"
            dep_md += "\n"

        sections.append(("Dependencies", "dependencies", dep_md))
        toc_entries.append((2, "Dependencies", "dependencies"))

    # -----------------------------------------------------------------------
    # JDK 17+/21 suggestions
    # -----------------------------------------------------------------------
    suggestions = result.get('suggestions', [])
    if suggestions:
        sugg_md = ""
        by_cat: Dict[str, List] = defaultdict(list)
        for s in suggestions:
            by_cat[s.get('category', 'jdk17')].append(s)
        for cat, items in sorted(by_cat.items()):
            sugg_md += f"### {cat.upper()} Suggestions\n\n"
            for s in items:
                line = s.get('line', '?')
                sugg_md += f"- **Line {line}:** {s.get('message', '')}"
                if s.get('suggestion'):
                    sugg_md += f" — *{s['suggestion']}*"
                sugg_md += "\n"
            sugg_md += "\n"
        sections.append(("Modern Java Suggestions", "modern-java-suggestions", sugg_md))
        toc_entries.append((2, "Modern Java Suggestions", "modern-java-suggestions"))

    # -----------------------------------------------------------------------
    # Metrics
    # -----------------------------------------------------------------------
    if 'metrics' in result:
        metrics = result['metrics']
        met_md = (
            f"| Metric | Value |\n|--------|-------|\n"
            f"| Total Lines | {metrics.get('total_lines', 0)} |\n"
            f"| Code Lines | {metrics.get('code_lines', 0)} |\n"
            f"| Comment Lines | {metrics.get('comment_lines', 0)} |\n"
            f"| Blank Lines | {metrics.get('blank_lines', 0)} |\n"
        )
        sections.append(("Metrics", "metrics", met_md))
        toc_entries.append((2, "Metrics", "metrics"))

    # -----------------------------------------------------------------------
    # Classes
    # -----------------------------------------------------------------------
    if result.get('classes'):
        cls_md = ""
        for cls in result['classes']:
            cls_md += f"### {cls.get('name', 'Unknown')}\n\n"
            cls_md += f"- **Type:** {'Record' if cls.get('is_record') else 'Class'}\n"
            if cls.get('extends'):
                cls_md += f"- **Extends:** {cls['extends']}\n"
            if cls.get('implements'):
                cls_md += f"- **Implements:** {', '.join(cls['implements'])}\n"
            cls_md += f"- **Fields:** {cls.get('fields_count', 0)}\n"
            cls_md += f"- **Methods:** {cls.get('methods_count', 0)}\n"
            cls_md += f"- **Lines:** {cls.get('lines', 0)}\n\n"
        sections.append(("Classes", "classes", cls_md))
        toc_entries.append((2, "Classes", "classes"))

    # -----------------------------------------------------------------------
    # Errors / parse issues
    # -----------------------------------------------------------------------
    if 'error' in result:
        sections.append(("Errors", "errors", f"**Error:** {result['error']}\n"))
        toc_entries.append((2, "Errors", "errors"))

    # -----------------------------------------------------------------------
    # Assemble final output
    # -----------------------------------------------------------------------
    md = md_header

    # Table of Contents (only for project reports with multiple sections)
    if len(sections) >= 3:
        md += "## Table of Contents\n\n"
        for level, label, anchor in toc_entries:
            indent = "  " * (level - 2)
            md += f"{indent}- [{label}](#{anchor})\n"
        md += "\n---\n\n"

    for heading, anchor, content in sections:
        md += f"## {heading}\n\n{content}"

    return md


# ---------------------------------------------------------------------------
# F10: Layer dependency matrix
# ---------------------------------------------------------------------------
def _render_dependency_matrix(packages_info: Dict) -> str:
    """Render a layer-level dependency matrix from package analysis data."""
    layers = {'domain': set(), 'adapter': set(), 'usecase': set(), 'other': set()}
    for pkg_name, pkg in packages_info.items():
        if pkg.get('is_domain'):
            layers['domain'].add(pkg_name)
        elif pkg.get('is_adapter'):
            layers['adapter'].add(pkg_name)
        elif pkg.get('is_usecase'):
            layers['usecase'].add(pkg_name)
        else:
            layers['other'].add(pkg_name)

    layer_names = [l for l in ['domain', 'adapter', 'usecase', 'other'] if layers[l]]
    if len(layer_names) < 2:
        return ""

    # Build adjacency: does layer A import from layer B?
    matrix: Dict[str, Dict[str, bool]] = {a: {b: False for b in layer_names} for a in layer_names}

    for pkg_name, pkg in packages_info.items():
        src_layer = next((l for l in layer_names if pkg_name in layers[l]), None)
        if not src_layer:
            continue
        for imp in pkg.get('imports', []):
            for tgt_layer in layer_names:
                if src_layer == tgt_layer:
                    continue
                for tgt_pkg in layers[tgt_layer]:
                    if imp == tgt_pkg or imp.startswith(tgt_pkg + '.'):
                        matrix[src_layer][tgt_layer] = True

    header = "| Layer | " + " | ".join(layer_names) + " |\n"
    separator = "|-------|" + "|---------|" * len(layer_names) + "\n"
    rows = ""
    for src in layer_names:
        row = f"| **{src}** |"
        for tgt in layer_names:
            if src == tgt:
                row += " — |"
            else:
                row += " ✓ |" if matrix[src][tgt] else " ✗ |"
        rows += row + "\n"

    return "### Layer Dependency Matrix\n\n" + header + separator + rows + "\n"

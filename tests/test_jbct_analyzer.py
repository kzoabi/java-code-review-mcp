"""Tests for src/tools/jbct_analyzer.py"""
import os
import pytest

FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures')


def issues_with_rule(result, rule):
    return [i for i in result.get('issues', []) if i.get('rule') == rule]


# ---------------------------------------------------------------------------
# Core JBCT rules against the JbctViolations fixture
# ---------------------------------------------------------------------------
class TestJbctReturnTypes:
    def test_return_null_detected(self, jbct_config):
        from src.tools.jbct_analyzer import run_jbct_analysis
        fp = os.path.join(FIXTURES, 'JbctViolations.java')
        result = run_jbct_analysis(fp, jbct_config, package='com.example.domain')
        assert issues_with_rule(result, 'JBCT-RET-03'), "Expected JBCT-RET-03 (return null)"

    def test_nested_wrapper_detected(self, jbct_config):
        from src.tools.jbct_analyzer import run_jbct_analysis
        fp = os.path.join(FIXTURES, 'JbctViolations.java')
        result = run_jbct_analysis(fp, jbct_config, package='com.example.domain')
        assert issues_with_rule(result, 'JBCT-RET-02'), "Expected JBCT-RET-02 (nested wrapper)"


class TestJbctExceptions:
    def test_throw_exception_detected(self, jbct_config):
        from src.tools.jbct_analyzer import run_jbct_analysis
        fp = os.path.join(FIXTURES, 'JbctViolations.java')
        result = run_jbct_analysis(fp, jbct_config, package='com.example.domain')
        assert issues_with_rule(result, 'JBCT-EX-01'), "Expected JBCT-EX-01 (throws clause)"


class TestJbctArchitecture:
    def test_io_in_domain_detected(self, jbct_config):
        from src.tools.jbct_analyzer import run_jbct_analysis
        fp = os.path.join(FIXTURES, 'JbctViolations.java')
        result = run_jbct_analysis(fp, jbct_config, package='com.example.domain')
        arch_issues = issues_with_rule(result, 'JBCT-MIX-01')
        assert arch_issues, "Expected JBCT-MIX-01 (I/O in domain)"

    def test_non_domain_package_no_arch_issue(self, jbct_config):
        from src.tools.jbct_analyzer import run_jbct_analysis
        fp = os.path.join(FIXTURES, 'JbctViolations.java')
        result = run_jbct_analysis(fp, jbct_config, package='com.example.adapter')
        arch_issues = issues_with_rule(result, 'JBCT-MIX-01')
        assert not arch_issues, "JBCT-MIX-01 should not fire for non-domain packages"


class TestJbctLambda:
    def test_complex_lambda_detected(self, jbct_config):
        from src.tools.jbct_analyzer import run_jbct_analysis
        fp = os.path.join(FIXTURES, 'JbctViolations.java')
        result = run_jbct_analysis(fp, jbct_config, package='com.example.domain')
        lambda_issues = issues_with_rule(result, 'JBCT-LAM-01')
        assert lambda_issues, "Expected JBCT-LAM-01 (complex lambda)"


# ---------------------------------------------------------------------------
# review_level filtering applied by jbct_analyzer (F7)
# ---------------------------------------------------------------------------
class TestJbctReviewLevelFiltering:
    def test_quick_mode_drops_style_issues(self, jbct_config, tmp_path):
        from src.tools.jbct_analyzer import run_jbct_analysis
        # Write a file that has style issues (Result.failure usage)
        fp = tmp_path / "Style.java"
        fp.write_text(
            "package com.example;\n"
            "import org.pragmatica.lang.Result;\n"
            "class Style { void m() { Result.failure(null); } }\n"
        )
        result = run_jbct_analysis(str(fp), jbct_config, review_level='quick')
        style_issues = [i for i in result.get('issues', []) if i.get('category') in ('style', 'naming')]
        assert not style_issues, "quick mode should suppress style/naming JBCT issues"

    def test_security_mode_returns_no_jbct_issues(self, jbct_config):
        from src.tools.jbct_analyzer import run_jbct_analysis
        fp = os.path.join(FIXTURES, 'JbctViolations.java')
        result = run_jbct_analysis(fp, jbct_config, package='com.example.domain', review_level='security')
        assert result.get('issues', []) == [], "security mode should suppress all JBCT issues"


# ---------------------------------------------------------------------------
# Disabled JBCT profile
# ---------------------------------------------------------------------------
class TestJbctDisabledProfile:
    def test_disabled_profile_returns_no_issues(self, default_config):
        from src.tools.jbct_analyzer import run_jbct_analysis
        fp = os.path.join(FIXTURES, 'JbctViolations.java')
        cfg = default_config.copy()
        cfg['jbct_profile'] = 'disabled'
        result = run_jbct_analysis(fp, cfg)
        assert result.get('issues', []) == []


# ---------------------------------------------------------------------------
# Missing file
# ---------------------------------------------------------------------------
class TestJbctMissingFile:
    def test_missing_file_returns_error(self, jbct_config):
        from src.tools.jbct_analyzer import run_jbct_analysis
        result = run_jbct_analysis('/nonexistent/Foo.java', jbct_config)
        assert 'error' in result

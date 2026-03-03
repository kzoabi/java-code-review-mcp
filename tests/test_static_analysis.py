"""Tests for src/tools/static_analysis.py"""
import asyncio
import os
import pytest

FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures')


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def issues_with_rule(result, rule):
    return [i for i in result.get('issues', []) if i.get('rule') == rule]


def categories(result):
    return {i.get('category') for i in result.get('issues', [])}


# ---------------------------------------------------------------------------
# Security rules
# ---------------------------------------------------------------------------
class TestSecurityRules:
    def test_hardcoded_credentials_detected(self, default_config):
        from src.tools.static_analysis import run_static_analysis
        fp = os.path.join(FIXTURES, 'SecurityIssues.java')
        result = run(run_static_analysis(fp, 'all', default_config))
        cred_issues = [i for i in result['issues'] if i.get('rule') == 'HardcodedCredentials']
        assert len(cred_issues) >= 1

    def test_sql_injection_detected(self, default_config):
        from src.tools.static_analysis import run_static_analysis
        fp = os.path.join(FIXTURES, 'SecurityIssues.java')
        result = run(run_static_analysis(fp, 'all', default_config))
        sql_issues = [i for i in result['issues'] if i.get('rule') == 'SQLInjection']
        assert len(sql_issues) >= 1

    def test_hardcoded_credentials_are_critical(self, default_config):
        from src.tools.static_analysis import run_static_analysis
        fp = os.path.join(FIXTURES, 'SecurityIssues.java')
        result = run(run_static_analysis(fp, 'all', default_config))
        cred_issues = [i for i in result['issues'] if i.get('rule') == 'HardcodedCredentials']
        assert all(i['severity'] == 'critical' for i in cred_issues)


# ---------------------------------------------------------------------------
# Empty catch block
# ---------------------------------------------------------------------------
class TestExceptionRules:
    def test_empty_catch_detected(self, default_config):
        from src.tools.static_analysis import run_static_analysis
        fp = os.path.join(FIXTURES, 'EmptyCatch.java')
        result = run(run_static_analysis(fp, 'all', default_config))
        catch_issues = [i for i in result['issues'] if i.get('rule') == 'EmptyCatchBlock']
        assert len(catch_issues) >= 1


# ---------------------------------------------------------------------------
# review_level filtering (F7)
# ---------------------------------------------------------------------------
class TestReviewLevelFiltering:
    def test_quick_mode_keeps_only_critical_major(self, default_config):
        from src.tools.static_analysis import run_static_analysis
        fp = os.path.join(FIXTURES, 'SecurityIssues.java')
        result = run(run_static_analysis(fp, 'all', default_config, review_level='quick'))
        for issue in result.get('issues', []):
            assert issue['severity'] in ('critical', 'major'), (
                f"quick mode should not include severity={issue['severity']}")

    def test_quick_mode_drops_style_category(self, default_config):
        from src.tools.static_analysis import run_static_analysis
        fp = os.path.join(FIXTURES, 'SecurityIssues.java')
        result = run(run_static_analysis(fp, 'all', default_config, review_level='quick'))
        assert 'style' not in categories(result)

    def test_quick_mode_drops_jdk_suggestions(self, default_config):
        from src.tools.static_analysis import run_static_analysis
        fp = os.path.join(FIXTURES, 'SecurityIssues.java')
        result = run(run_static_analysis(fp, 'all', default_config, review_level='quick'))
        assert result.get('jdk17_suggestions', []) == []

    def test_security_mode_keeps_only_security(self, default_config):
        from src.tools.static_analysis import run_static_analysis
        fp = os.path.join(FIXTURES, 'SecurityIssues.java')
        result = run(run_static_analysis(fp, 'all', default_config, review_level='security'))
        for issue in result.get('issues', []):
            assert issue.get('category') == 'security', (
                f"security mode should not include category={issue.get('category')}")

    def test_security_mode_drops_jbct(self, default_config):
        from src.tools.static_analysis import run_static_analysis
        fp = os.path.join(FIXTURES, 'SecurityIssues.java')
        cfg = default_config.copy()
        cfg['jbct_profile'] = 'full'
        result = run(run_static_analysis(fp, 'all', cfg, review_level='security'))
        assert result.get('jbct_issues', []) == []

    def test_full_mode_includes_all(self, default_config):
        from src.tools.static_analysis import run_static_analysis
        fp = os.path.join(FIXTURES, 'SecurityIssues.java')
        result = run(run_static_analysis(fp, 'all', default_config, review_level='full'))
        # Full mode should not strip any category — just check it doesn't crash
        assert 'issues' in result


# ---------------------------------------------------------------------------
# Java 21 suggestions (F2)
# ---------------------------------------------------------------------------
class TestJava21Suggestions:
    def _write_tmp(self, tmp_path, code):
        p = tmp_path / "Tmp.java"
        p.write_text(code)
        return str(p)

    def test_virtual_thread_suggestion(self, tmp_path, default_config):
        from src.tools.static_analysis import run_static_analysis
        fp = self._write_tmp(tmp_path, "class T { void m() { new Thread(() -> {}).start(); } }")
        cfg = default_config.copy()
        cfg['jdk21_features'] = {'recommend_virtual_threads': True,
                                  'recommend_structured_concurrency': False,
                                  'recommend_string_templates': False}
        result = run(run_static_analysis(fp, 'all', cfg))
        jdk21 = [s for s in result.get('jdk17_suggestions', []) if s.get('category') == 'jdk21']
        assert len(jdk21) >= 1

    def test_no_virtual_thread_suggestion_when_disabled(self, tmp_path, default_config):
        from src.tools.static_analysis import run_static_analysis
        fp = self._write_tmp(tmp_path, "class T { void m() { new Thread(() -> {}).start(); } }")
        cfg = default_config.copy()
        cfg['jdk21_features'] = {'recommend_virtual_threads': False,
                                  'recommend_structured_concurrency': False,
                                  'recommend_string_templates': False}
        result = run(run_static_analysis(fp, 'all', cfg))
        jdk21 = [s for s in result.get('jdk17_suggestions', []) if s.get('category') == 'jdk21']
        assert len(jdk21) == 0


# ---------------------------------------------------------------------------
# Missing file
# ---------------------------------------------------------------------------
class TestMissingFile:
    def test_missing_file_returns_error(self, default_config):
        from src.tools.static_analysis import run_static_analysis
        result = run(run_static_analysis('/nonexistent/path/Foo.java', 'all', default_config))
        assert 'error' in result

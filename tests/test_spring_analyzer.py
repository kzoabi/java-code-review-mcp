"""Tests for src/tools/spring_analyzer.py"""
import os
import pytest

FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures')


def issues_with_rule(result, rule):
    return [i for i in result.get('issues', []) if i.get('rule') == rule]


class TestTransactional:
    def test_transactional_on_private_detected(self, spring_config):
        from src.tools.spring_analyzer import run_spring_analysis
        fp = os.path.join(FIXTURES, 'SpringIssues.java')
        result = run_spring_analysis(fp, spring_config)
        tx_issues = issues_with_rule(result, 'SPRING-TX-01')
        assert tx_issues, "Expected SPRING-TX-01 for @Transactional on private method"

    def test_transactional_on_public_not_flagged(self, spring_config, tmp_path):
        from src.tools.spring_analyzer import run_spring_analysis
        fp = tmp_path / "Ok.java"
        fp.write_text("""
import org.springframework.transaction.annotation.Transactional;
class Ok {
    @Transactional
    public void save() {}
}
""")
        result = run_spring_analysis(str(fp), spring_config)
        tx_issues = issues_with_rule(result, 'SPRING-TX-01')
        assert not tx_issues


class TestFieldInjection:
    def test_field_autowired_detected(self, spring_config):
        from src.tools.spring_analyzer import run_spring_analysis
        fp = os.path.join(FIXTURES, 'SpringIssues.java')
        result = run_spring_analysis(fp, spring_config)
        di_issues = issues_with_rule(result, 'SPRING-DI-01')
        assert di_issues, "Expected SPRING-DI-01 for @Autowired field injection"

    def test_constructor_injection_not_flagged(self, spring_config, tmp_path):
        from src.tools.spring_analyzer import run_spring_analysis
        fp = tmp_path / "Clean.java"
        fp.write_text("""
import org.springframework.beans.factory.annotation.Autowired;
class Clean {
    private final Svc svc;
    @Autowired
    public Clean(Svc svc) { this.svc = svc; }
}
class Svc {}
""")
        result = run_spring_analysis(str(fp), spring_config)
        di_issues = issues_with_rule(result, 'SPRING-DI-01')
        assert not di_issues


class TestValueFallback:
    def test_value_hardcoded_fallback_detected(self, spring_config):
        from src.tools.spring_analyzer import run_spring_analysis
        fp = os.path.join(FIXTURES, 'SpringIssues.java')
        result = run_spring_analysis(fp, spring_config)
        cfg_issues = issues_with_rule(result, 'SPRING-CONFIG-01')
        assert cfg_issues, "Expected SPRING-CONFIG-01 for @Value with hardcoded fallback"


class TestRestController:
    def test_raw_return_type_detected(self, spring_config):
        from src.tools.spring_analyzer import run_spring_analysis
        fp = os.path.join(FIXTURES, 'SpringIssues.java')
        result = run_spring_analysis(fp, spring_config)
        rest_issues = issues_with_rule(result, 'SPRING-REST-01')
        assert rest_issues, "Expected SPRING-REST-01 for raw return type in @RestController"


class TestSpringDisabled:
    def test_disabled_returns_no_issues(self, default_config):
        from src.tools.spring_analyzer import run_spring_analysis
        fp = os.path.join(FIXTURES, 'SpringIssues.java')
        cfg = default_config.copy()
        cfg['spring_enabled'] = False
        result = run_spring_analysis(fp, cfg)
        assert result.get('issues', []) == []


class TestMissingFile:
    def test_missing_file_returns_error(self, spring_config):
        from src.tools.spring_analyzer import run_spring_analysis
        result = run_spring_analysis('/nonexistent/Spring.java', spring_config)
        assert 'error' in result

"""Integration tests for src/tools/code_review.py"""
import asyncio
import os
import pytest

FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures')
SAMPLE_FILES = os.path.join(os.path.dirname(__file__), 'sample_files')


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# review_file
# ---------------------------------------------------------------------------
class TestReviewFile:
    def test_bad_code_has_issues(self, default_config):
        from src.tools.code_review import review_file
        fp = os.path.join(SAMPLE_FILES, 'BadCodeExample.java')
        result = run(review_file(fp, 'full', default_config))
        assert 'issues' in result
        assert len(result['issues']) > 0

    def test_missing_file_returns_error(self, default_config):
        from src.tools.code_review import review_file
        result = run(review_file('/no/such/file.java', 'full', default_config))
        assert 'error' in result

    def test_quick_mode_fewer_issues_than_full(self, default_config):
        from src.tools.code_review import review_file
        fp = os.path.join(SAMPLE_FILES, 'BadCodeExample.java')
        full = run(review_file(fp, 'full', default_config))
        quick = run(review_file(fp, 'quick', default_config))
        # quick mode must not return more issues than full mode
        assert len(quick.get('issues', [])) <= len(full.get('issues', []))


# ---------------------------------------------------------------------------
# review_project — architecture is now included (F5)
# ---------------------------------------------------------------------------
class TestReviewProject:
    def test_project_review_includes_architecture(self, default_config, tmp_path):
        from src.tools.code_review import review_project
        # Copy a fixture into a temp dir to simulate a project
        src_dir = tmp_path / "src" / "main" / "java"
        src_dir.mkdir(parents=True)
        import shutil
        shutil.copy(
            os.path.join(SAMPLE_FILES, 'BadCodeExample.java'),
            str(src_dir / 'BadCodeExample.java')
        )
        result = run(review_project(str(tmp_path), 'full', default_config,
                                    include_deps=False, use_cache=False))
        assert 'architecture_issues' in result
        assert 'files_reviewed' in result
        assert result['files_reviewed'] >= 1

    def test_project_summary_present(self, default_config, tmp_path):
        from src.tools.code_review import review_project
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        import shutil
        shutil.copy(
            os.path.join(SAMPLE_FILES, 'BadCodeExample.java'),
            str(src_dir / 'BadCodeExample.java')
        )
        result = run(review_project(str(tmp_path), 'full', default_config,
                                    include_deps=False, use_cache=False))
        summary = result.get('summary', {})
        assert 'total_files' in summary
        assert 'total_issues' in summary

    def test_project_caching_produces_same_results(self, default_config, tmp_path):
        from src.tools.code_review import review_project
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        import shutil
        shutil.copy(
            os.path.join(SAMPLE_FILES, 'BadCodeExample.java'),
            str(src_dir / 'BadCodeExample.java')
        )
        first = run(review_project(str(tmp_path), 'full', default_config,
                                   include_deps=False, use_cache=True))
        second = run(review_project(str(tmp_path), 'full', default_config,
                                    include_deps=False, use_cache=True))
        assert first['files_reviewed'] == second['files_reviewed']
        assert len(first['issues']) == len(second['issues'])


# ---------------------------------------------------------------------------
# review_git_diff — ref / staged params (F4)
# ---------------------------------------------------------------------------
class TestReviewGitDiff:
    def test_invalid_repo_returns_error(self, default_config, tmp_path):
        from src.tools.code_review import review_git_diff
        result = run(review_git_diff(str(tmp_path), 'full', default_config))
        assert 'error' in result

    def test_ref_param_passed_to_git(self, default_config, tmp_path, monkeypatch):
        """Verify that ref is appended to the git command."""
        captured = []

        async def fake_exec(*args, **kwargs):
            captured.extend(args)

            class FakeProc:
                returncode = 1
                async def communicate(self):
                    return b'', b''
            return FakeProc()

        import asyncio as _asyncio
        monkeypatch.setattr(_asyncio, 'create_subprocess_exec', fake_exec)
        from src.tools.code_review import review_git_diff
        run(review_git_diff(str(tmp_path), 'full', default_config, ref='HEAD~1'))
        assert 'HEAD~1' in captured

    def test_staged_param_adds_cached_flag(self, default_config, tmp_path, monkeypatch):
        captured = []

        async def fake_exec(*args, **kwargs):
            captured.extend(args)

            class FakeProc:
                returncode = 1
                async def communicate(self):
                    return b'', b''
            return FakeProc()

        import asyncio as _asyncio
        monkeypatch.setattr(_asyncio, 'create_subprocess_exec', fake_exec)
        from src.tools.code_review import review_git_diff
        run(review_git_diff(str(tmp_path), 'full', default_config, staged=True))
        assert '--cached' in captured


# ---------------------------------------------------------------------------
# report_generator smoke test
# ---------------------------------------------------------------------------
class TestReportGenerator:
    def test_markdown_report_has_summary(self, default_config):
        from src.tools.code_review import review_file
        from src.tools.report_generator import generate_report
        fp = os.path.join(SAMPLE_FILES, 'BadCodeExample.java')
        result = run(review_file(fp, 'full', default_config))
        report = generate_report(result, 'markdown')
        assert '# Java Code Review Report' in report

    def test_json_report_is_valid(self, default_config):
        import json
        from src.tools.code_review import review_file
        from src.tools.report_generator import generate_report
        fp = os.path.join(SAMPLE_FILES, 'BadCodeExample.java')
        result = run(review_file(fp, 'full', default_config))
        report = generate_report(result, 'json')
        parsed = json.loads(report)
        assert 'issues' in parsed

    def test_sarif_report_is_valid(self, default_config):
        import json
        from src.tools.code_review import review_file
        from src.tools.report_generator import generate_report
        fp = os.path.join(SAMPLE_FILES, 'BadCodeExample.java')
        result = run(review_file(fp, 'full', default_config))
        report = generate_report(result, 'sarif')
        parsed = json.loads(report)
        assert parsed['version'] == '2.1.0'
        assert 'runs' in parsed

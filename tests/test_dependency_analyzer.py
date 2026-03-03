"""Tests for src/tools/dependency_analyzer.py (multi-module aware)"""
import asyncio
import os
import pytest

FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures')


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Maven
# ---------------------------------------------------------------------------
class TestMavenAnalysis:
    def test_parses_dependencies(self, tmp_path):
        from src.tools.dependency_analyzer import analyze_maven
        pom = tmp_path / "pom.xml"
        pom.write_text("""<?xml version="1.0"?>
<project>
  <dependencies>
    <dependency>
      <groupId>org.springframework</groupId>
      <artifactId>spring-core</artifactId>
      <version>6.1.0</version>
    </dependency>
  </dependencies>
</project>""")
        result = run(analyze_maven(str(tmp_path)))
        assert result['build_tool'] == 'maven'
        assert len(result['dependencies']) >= 1
        dep = result['dependencies'][0]
        assert dep['group'] == 'org.springframework'
        assert dep['artifact'] == 'spring-core'
        assert dep['version'] == '6.1.0'

    def test_flags_missing_version(self, tmp_path):
        from src.tools.dependency_analyzer import analyze_maven
        pom = tmp_path / "pom.xml"
        pom.write_text("""<?xml version="1.0"?>
<project>
  <dependencies>
    <dependency>
      <groupId>com.example</groupId>
      <artifactId>no-version</artifactId>
    </dependency>
  </dependencies>
</project>""")
        result = run(analyze_maven(str(tmp_path)))
        issues = [i for i in result.get('issues', []) if 'No version' in i.get('issue', '')]
        assert issues, "Should flag missing version"

    def test_multimodule_detects_version_conflict(self, tmp_path):
        from src.tools.dependency_analyzer import analyze_maven
        # root pom
        (tmp_path / "pom.xml").write_text("""<?xml version="1.0"?>
<project>
  <dependencies>
    <dependency>
      <groupId>com.google.guava</groupId>
      <artifactId>guava</artifactId>
      <version>31.0-jre</version>
    </dependency>
  </dependencies>
</project>""")
        # sub-module pom
        submod = tmp_path / "moduleA"
        submod.mkdir()
        (submod / "pom.xml").write_text("""<?xml version="1.0"?>
<project>
  <dependencies>
    <dependency>
      <groupId>com.google.guava</groupId>
      <artifactId>guava</artifactId>
      <version>32.1.2-jre</version>
    </dependency>
  </dependencies>
</project>""")
        result = run(analyze_maven(str(tmp_path)))
        assert len(result['modules']) == 2
        conflicts = result.get('version_conflicts', [])
        guava_conflict = [c for c in conflicts if 'guava' in c['dependency']]
        assert guava_conflict, "Should detect guava version conflict across modules"

    def test_missing_pom_returns_error(self, tmp_path):
        from src.tools.dependency_analyzer import analyze_maven
        result = run(analyze_maven(str(tmp_path)))
        assert 'error' in result


# ---------------------------------------------------------------------------
# Gradle
# ---------------------------------------------------------------------------
class TestGradleAnalysis:
    def test_parses_dependencies(self, tmp_path):
        from src.tools.dependency_analyzer import analyze_gradle
        gradle = tmp_path / "build.gradle"
        gradle.write_text("""
dependencies {
    implementation 'org.springframework.boot:spring-boot-starter:3.2.0'
    testImplementation 'org.junit.jupiter:junit-jupiter:5.10.0'
}
""")
        result = run(analyze_gradle(str(tmp_path)))
        assert result['build_tool'] == 'gradle'
        groups = {d['group'] for d in result['dependencies']}
        assert 'org.springframework.boot' in groups

    def test_multimodule_aggregates_deps(self, tmp_path):
        from src.tools.dependency_analyzer import analyze_gradle
        (tmp_path / "build.gradle").write_text("""
dependencies {
    implementation 'com.google.guava:guava:31.0-jre'
}
""")
        sub = tmp_path / "api"
        sub.mkdir()
        (sub / "build.gradle").write_text("""
dependencies {
    implementation 'com.google.guava:guava:32.1.2-jre'
}
""")
        result = run(analyze_gradle(str(tmp_path)))
        assert len(result['modules']) == 2
        guava_deps = [d for d in result['dependencies'] if 'guava' in d['artifact']]
        assert len(guava_deps) == 2
        conflicts = [c for c in result.get('version_conflicts', []) if 'guava' in c['dependency']]
        assert conflicts, "Should detect guava version conflict"

    def test_missing_gradle_returns_error(self, tmp_path):
        from src.tools.dependency_analyzer import analyze_gradle
        result = run(analyze_gradle(str(tmp_path)))
        assert 'error' in result


# ---------------------------------------------------------------------------
# Auto-detection
# ---------------------------------------------------------------------------
class TestAutoDetection:
    def test_auto_detects_maven(self, tmp_path):
        from src.tools.dependency_analyzer import analyze_dependencies
        (tmp_path / "pom.xml").write_text("""<?xml version="1.0"?>
<project><dependencies></dependencies></project>""")
        result = run(analyze_dependencies(str(tmp_path), 'auto'))
        assert result['build_tool'] == 'maven'

    def test_auto_detects_gradle(self, tmp_path):
        from src.tools.dependency_analyzer import analyze_dependencies
        (tmp_path / "build.gradle").write_text("dependencies {}")
        result = run(analyze_dependencies(str(tmp_path), 'auto'))
        assert result['build_tool'] == 'gradle'

    def test_no_build_file_returns_error(self, tmp_path):
        from src.tools.dependency_analyzer import analyze_dependencies
        result = run(analyze_dependencies(str(tmp_path), 'auto'))
        assert 'error' in result

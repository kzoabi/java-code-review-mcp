"""Tests for src/tools/git_diff_parser.py"""
import pytest
from src.tools.git_diff_parser import parse_git_diff


SAMPLE_DIFF = """\
diff --git a/src/Foo.java b/src/Foo.java
index 1234567..abcdefg 100644
--- a/src/Foo.java
+++ b/src/Foo.java
@@ -1,5 +1,6 @@
 package com.example;
+import java.util.List;
 public class Foo {
-    int x = 1;
+    int x = 2;
 }
"""

DELETED_FILE_DIFF = """\
diff --git a/src/Old.java b/src/Old.java
deleted file mode 100644
index 1234567..0000000
--- a/src/Old.java
+++ /dev/null
@@ -1,3 +0,0 @@
-package com.example;
-public class Old {}
"""

RENAMED_FILE_DIFF = """\
diff --git a/src/OldName.java b/src/NewName.java
similarity index 100%
rename from src/OldName.java
rename to src/NewName.java
"""

MULTI_FILE_DIFF = """\
diff --git a/src/A.java b/src/A.java
--- a/src/A.java
+++ b/src/A.java
@@ -1,1 +1,1 @@
-int a = 1;
+int a = 2;
diff --git a/src/B.java b/src/B.java
--- a/src/B.java
+++ b/src/B.java
@@ -1,1 +1,1 @@
-int b = 1;
+int b = 2;
"""


class TestParseGitDiff:
    def test_basic_diff_parsed(self):
        changes = parse_git_diff(SAMPLE_DIFF)
        assert len(changes) == 1
        assert changes[0]['file_path'] == 'src/Foo.java'

    def test_additions_captured(self):
        changes = parse_git_diff(SAMPLE_DIFF)
        additions = changes[0]['additions']
        assert any('import java.util.List' in a for a in additions)
        assert any('int x = 2' in a for a in additions)

    def test_deletions_captured(self):
        changes = parse_git_diff(SAMPLE_DIFF)
        deletions = changes[0]['deletions']
        assert any('int x = 1' in d for d in deletions)

    def test_deleted_file_included(self):
        """Deleted files should appear with file_path from diff --git header."""
        changes = parse_git_diff(DELETED_FILE_DIFF)
        assert len(changes) == 1
        assert changes[0]['file_path'] == 'src/Old.java'

    def test_deleted_file_has_deletions(self):
        changes = parse_git_diff(DELETED_FILE_DIFF)
        assert len(changes[0]['deletions']) >= 1

    def test_multi_file_diff(self):
        changes = parse_git_diff(MULTI_FILE_DIFF)
        assert len(changes) == 2
        paths = {c['file_path'] for c in changes}
        assert 'src/A.java' in paths
        assert 'src/B.java' in paths

    def test_empty_diff(self):
        changes = parse_git_diff('')
        assert changes == []

    def test_no_java_files_returns_all_changes(self):
        diff = """\
diff --git a/README.md b/README.md
--- a/README.md
+++ b/README.md
@@ -1 +1 @@
-old
+new
"""
        changes = parse_git_diff(diff)
        assert len(changes) == 1
        assert changes[0]['file_path'] == 'README.md'

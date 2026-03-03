"""Git Diff Parser Module"""
import re
from typing import Dict, List, Any

def parse_git_diff(diff_output: str) -> List[Dict]:
    """Parse git diff output into structured changes."""
    changes = []
    current_file = None
    current_changes = {'additions': [], 'deletions': []}
    lines = diff_output.split('\n')
    for line in lines:
        if line.startswith('diff --git'):
            if current_file:
                changes.append({'file_path': current_file, **current_changes})
            # Extract filename from header as fallback for deleted files (no +++ b/... line)
            git_match = re.match(r'diff --git a/.+ b/(.+)', line)
            current_file = git_match.group(1) if git_match else None
            current_changes = {'additions': [], 'deletions': []}
        elif line.startswith('+++'):
            # +++ /dev/null means deleted file; keep the name from the diff --git header
            match = re.match(r'\+\+\+ b/(.+)', line)
            if match:
                current_file = match.group(1)
        elif line.startswith('@@'):
            pass
        elif line.startswith('+') and not line.startswith('+++'):
            if current_file:
                current_changes['additions'].append(line[1:])
        elif line.startswith('-') and not line.startswith('---'):
            if current_file:
                current_changes['deletions'].append(line[1:])
    if current_file:
        changes.append({'file_path': current_file, **current_changes})
    return changes

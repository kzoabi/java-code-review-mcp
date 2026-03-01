"""Git Diff Parser Module"""
import re
from typing import Dict, List, Any

def parse_git_diff(diff_output: str) -> List[Dict]:
    """Parse git diff output into structured changes."""
    changes = []
    current_file = None
    current_changes = {'additions': [], 'deletions': [], 'modifications': []}
    lines = diff_output.split('\n')
    for line in lines:
        if line.startswith('diff --git'):
            if current_file:
                changes.append({'file_path': current_file, **current_changes})
            current_file = None
            current_changes = {'additions': [], 'deletions': [], 'modifications': []}
        elif line.startswith('+++') or line.startswith('---'):
            if line.startswith('+++'):
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

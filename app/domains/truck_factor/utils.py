from typing import List, Dict, Any


def parse_gitlog_to_commits(report_lines: List[str]) -> List[Dict[str, Any]]:
    commits = []
    current_commit = None

    for line in report_lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith('COMMIT|'):
            parts = line.split('|')
            author = parts[2] if len(parts) > 2 else "Unknown"
            current_commit = {'author': author, 'files': []}
            commits.append(current_commit)
        elif current_commit is not None:
            current_commit['files'].append(line)

    return commits

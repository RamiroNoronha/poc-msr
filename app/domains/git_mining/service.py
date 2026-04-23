from typing import List, Dict, Any
from .contracts import GitMinerProtocol


class GitMiningService:
    def __init__(self, miner: GitMinerProtocol):
        self.miner = miner

    def process_gitlog(self, clone_url: str) -> List[Dict[str, Any]]:
        raw_log_lines = self.miner.generate_gitlog_report(clone_url)

        parsed_commits = []
        current_commit = None

        for line in raw_log_lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("COMMIT|"):
                parts = line.split('|')
                current_commit = {
                    "hash": parts[1] if len(parts) > 1 else "",
                    "author": parts[2] if len(parts) > 2 else "",
                    "date": parts[3] if len(parts) > 3 else "",
                    "message": parts[4] if len(parts) > 4 else "",
                    "files_touched": []
                }
                parsed_commits.append(current_commit)

            elif current_commit is not None:
                current_commit["files_touched"].append(line)

        return parsed_commits

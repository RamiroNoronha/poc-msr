from typing import List, Dict, Any, Tuple
from collections import Counter
from .contracts import GitMinerProtocol


class GitMiningService:
    def __init__(self, miner: GitMinerProtocol):
        self.miner = miner
        self.size_fall_back = 10

    def process_gitlog(self, clone_url: str) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        raw_log_lines, file_sizes = self.miner.generate_gitlog_report(
            clone_url)

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

        return parsed_commits, file_sizes

    def get_d3_hierarchical_data(self, clone_url: str) -> Dict[str, Any]:
        commits, file_sizes = self.process_gitlog(clone_url)

        file_revisions = Counter()
        for commit in commits:
            for file_path in commit["files_touched"]:
                file_revisions[file_path] += 1

        max_revisions = max(file_revisions.values()) if file_revisions else 1

        return self._build_d3_hierarchy(file_revisions, max_revisions, file_sizes)

    def _build_d3_hierarchy(self, file_revisions: Counter, max_revisions: int, file_sizes: Dict[str, int]) -> Dict[str, Any]:
        root = {"name": "root", "children": []}

        for file_path, revisions in file_revisions.items():
            parts = file_path.split("/")
            current_level = root

            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    weight = revisions / max_revisions

                    real_size = file_sizes.get(file_path, self.size_fall_back)

                    current_level["children"].append({
                        "name": part,
                        "size": real_size,
                        "weight": float(f"{weight:.4f}"),
                        "revisions": revisions
                    })
                else:
                    found = False
                    for child in current_level["children"]:
                        if child["name"] == part and "children" in child:
                            current_level = child
                            found = True
                            break

                    if not found:
                        new_dir = {"name": part, "children": []}
                        current_level["children"].append(new_dir)
                        current_level = new_dir

        return root

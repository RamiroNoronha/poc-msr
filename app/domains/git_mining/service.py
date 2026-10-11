from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
from .contracts import GitMinerProtocol
from .identity import build_identity_map, identity_id, list_developers, suggest_groups


class GitMiningService:
    def __init__(self, miner: GitMinerProtocol):
        self.miner = miner
        self.size_fall_back = 10

    def process_gitlog(
        self,
        clone_url: str,
        branch: Optional[str] = None,
        groups: Optional[List[List[str]]] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        raw_log_lines, file_sizes = self.miner.generate_gitlog_report(
            clone_url, branch)

        parsed_commits = []
        current_commit = None

        for line in raw_log_lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("COMMIT|"):
                parts = line.split('|', 5)
                current_commit = {
                    "hash": parts[1] if len(parts) > 1 else "",
                    "author": parts[2] if len(parts) > 2 else "",
                    "email": parts[3] if len(parts) > 3 else "",
                    "date": parts[4] if len(parts) > 4 else "",
                    "message": parts[5] if len(parts) > 5 else "",
                    "files_touched": []
                }
                parsed_commits.append(current_commit)

            elif current_commit is not None:
                current_commit["files_touched"].append(line)

        if groups:
            identity_map = build_identity_map(parsed_commits, groups)
            for commit in parsed_commits:
                key = identity_id(commit["author"], commit["email"])
                commit["author"] = identity_map.get(key, commit["author"])

        return parsed_commits, file_sizes

    def get_developers(self, clone_url: str, branch: Optional[str] = None) -> Dict[str, Any]:
        commits, _ = self.process_gitlog(clone_url, branch)
        developers = list_developers(commits)

        return {
            "developers": developers,
            "suggested_groups": suggest_groups(developers)
        }

    def get_d3_hierarchical_data(
        self,
        clone_url: str,
        branch: Optional[str] = None,
        groups: Optional[List[List[str]]] = None
    ) -> Dict[str, Any]:
        commits, file_sizes = self.process_gitlog(clone_url, branch, groups)

        file_revisions = Counter()
        file_authors: Dict[str, Counter] = {}
        for commit in commits:
            for file_path in commit["files_touched"]:
                file_revisions[file_path] += 1
                file_authors.setdefault(
                    file_path, Counter())[commit["author"]] += 1

        max_revisions = max(file_revisions.values()) if file_revisions else 1

        return self._build_d3_hierarchy(file_revisions, max_revisions, file_sizes, file_authors)

    def _build_d3_hierarchy(
        self,
        file_revisions: Counter,
        max_revisions: int,
        file_sizes: Dict[str, int],
        file_authors: Optional[Dict[str, Counter]] = None
    ) -> Dict[str, Any]:
        root = {"name": "root", "children": []}

        for file_path, revisions in file_revisions.items():
            parts = file_path.split("/")
            current_level = root

            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    weight = revisions / max_revisions

                    real_size = file_sizes.get(file_path, self.size_fall_back)

                    file_node = {
                        "name": part,
                        "size": real_size,
                        "weight": float(f"{weight:.4f}"),
                        "revisions": revisions
                    }

                    if file_authors is not None:
                        file_node["authors"] = [
                            {"name": name, "revisions": count}
                            for name, count in file_authors[file_path].most_common()
                        ]

                    current_level["children"].append(file_node)
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

    def get_author_d3_hierarchical_data(self, clone_url: str, author_name: str, branch: Optional[str] = None) -> Dict[str, Any]:
        commits, file_sizes = self.process_gitlog(clone_url, branch)

        filtered_commits = [
            c for c in commits
            if c["author"].lower() == author_name.lower()
        ]

        file_revisions = Counter()
        for commit in filtered_commits:
            for file_path in commit["files_touched"]:
                file_revisions[file_path] += 1

        max_revisions = max(file_revisions.values()) if file_revisions else 1

        return self._build_d3_hierarchy(file_revisions, max_revisions, file_sizes)

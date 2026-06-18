import math
from typing import List, Dict, Any, Optional, Set
from app.domains.git_mining.service import GitMiningService


class TruckFactorService:
    def __init__(self, git_mining_service: GitMiningService):
        self.git_mining_service = git_mining_service
        self.DOA_BASE = 3.293
        self.DOA_FA_WEIGHT = 1.098
        self.DOA_DL_WEIGHT = 0.164
        self.DOA_AC_WEIGHT = 0.321
        self.OWNERSHIP_THRESHOLD = 0.75

    def _calculate_doa_value(self, fa: int, dl: int, ac: int) -> float:
        return self.DOA_BASE + (self.DOA_FA_WEIGHT * fa) + (self.DOA_DL_WEIGHT * dl) - (self.DOA_AC_WEIGHT * math.log(1 + ac))

    def calculate_system_authorship(self, commits: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        authorship_matrix: Dict[str, Dict[str, Any]] = {}

        for commit in commits:
            author = commit.get("author", "Unknown")
            files_changed = commit.get("files_touched", [])

            for file_path in files_changed:
                if file_path not in authorship_matrix:
                    authorship_matrix[file_path] = {}

                if not authorship_matrix[file_path]:
                    authorship_matrix[file_path][author] = {
                        "FA": 1, "DL": 1, "AC": 0}
                else:
                    if author not in authorship_matrix[file_path]:
                        authorship_matrix[file_path][author] = {
                            "FA": 0, "DL": 1, "AC": 0}
                    else:
                        authorship_matrix[file_path][author]["DL"] += 1

                    for existing_author in authorship_matrix[file_path]:
                        if existing_author != author:
                            authorship_matrix[file_path][existing_author]["AC"] += 1

        doa_results: Dict[str, Dict[str, float]] = {}
        for file_path, authors_data in authorship_matrix.items():
            doa_results[file_path] = {}
            for author_name, metrics in authors_data.items():
                doa_value = self._calculate_doa_value(
                    metrics["FA"], metrics["DL"], metrics["AC"])
                doa_results[file_path][author_name] = doa_value

        return doa_results

    def determine_principal_authors(self, doa_matrix: Dict[str, Dict[str, float]]) -> Dict[str, List[str]]:
        principal_authors_by_file: Dict[str, List[str]] = {}

        for file_path, authors_doa in doa_matrix.items():
            if not authors_doa:
                principal_authors_by_file[file_path] = []
                continue

            doa_values = list(authors_doa.values())
            max_doa = max(doa_values) if doa_values else 0.0

            principal_authors: List[str] = []

            if max_doa > 0:
                for author, doa_value in authors_doa.items():
                    normalized_doa = doa_value / max_doa
                    if normalized_doa > self.OWNERSHIP_THRESHOLD:
                        principal_authors.append(author)

            principal_authors_by_file[file_path] = principal_authors

        return principal_authors_by_file

    def calculate_truck_factor(self, principal_authors: Dict[str, List[str]]) -> Dict[str, Any]:
        total_files = len(principal_authors)
        if total_files == 0:
            return {"truck_factor": 0, "key_developers": []}

        current_authors = {f: list(authors)
                           for f, authors in principal_authors.items()}
        active_developers: Set[str] = set()
        for authors in principal_authors.values():
            active_developers.update(authors)

        truck_factor = 0
        key_developers: List[str] = []

        while True:
            orphaned_files = sum(
                1 for f, authors in current_authors.items() if len(authors) == 0)
            if orphaned_files > (total_files / 2):
                break

            if not active_developers:
                break

            developer_coverage: Dict[str, int] = {
                dev: 0 for dev in active_developers}
            for authors in current_authors.values():
                for dev in authors:
                    if dev in developer_coverage:
                        developer_coverage[dev] += 1

            coverage_values = list(developer_coverage.values())
            if not coverage_values or max(coverage_values) == 0:
                break

            top_developer = max(list(developer_coverage.keys()),
                                key=lambda k: developer_coverage[k])
            key_developers.append(top_developer)
            active_developers.remove(top_developer)
            truck_factor += 1

            for file_path in current_authors:
                if top_developer in current_authors[file_path]:
                    current_authors[file_path].remove(top_developer)

        return {
            "truck_factor": truck_factor,
            "key_developers": key_developers
        }

    def get_truck_factor_report(self, repo_url: str, branch: Optional[str] = None) -> Dict[str, Any]:
        commits, _ = self.git_mining_service.process_gitlog(repo_url, branch)
        doa_matrix = self.calculate_system_authorship(commits)
        ownership_map = self.determine_principal_authors(doa_matrix)
        result = self.calculate_truck_factor(ownership_map)

        return {
            "truck_factor": result["truck_factor"],
            "key_developers": result["key_developers"],
            "total_files_analyzed": len(ownership_map)
        }

from typing import List, Protocol, Tuple, Dict


class GitMinerProtocol(Protocol):

    def generate_gitlog_report(self, repo_url: str) -> Tuple[List[str], Dict[str, int]]:
        ...

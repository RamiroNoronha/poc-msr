from typing import List, Optional, Protocol, Tuple, Dict


class GitMinerProtocol(Protocol):

    def generate_gitlog_report(self, repo_url: str, branch: Optional[str] = None) -> Tuple[List[str], Dict[str, int]]:
        ...

from typing import List, Protocol


class GitMinerProtocol(Protocol):

    def generate_gitlog_report(self, repo_url: str) -> List[str]:
        ...

import httpx
from typing import List, Dict, Any
from app.core.config import settings


class GitHubClient:
    def __init__(self):
        self.base_url = settings.GITHUB_API_URL
        self.headers = {
            "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "POC-MSR-App"
        }

    async def get_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(headers=self.headers) as client:
            response = await client.get(f"{self.base_url}/repos/{owner}/{repo}")
            response.raise_for_status()
            return response.json()

    async def get_contributors(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(headers=self.headers) as client:
            response = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}/contributors",
                params={"per_page": 100}
            )
            response.raise_for_status()
            return response.json()


github_client = GitHubClient()

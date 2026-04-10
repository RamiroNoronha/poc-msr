from fastapi import APIRouter, HTTPException
from app.infrastructure.github_client import github_client

router = APIRouter()


@router.get("/repo/{owner}/{repo}")
async def get_repository_info(owner: str, repo: str):
    try:
        data = await github_client.get_repository(owner, repo)
        return {
            "full_name": data["full_name"],
            "description": data["description"],
            "stars": data["stargazers_count"],
            "forks": data["forks_count"],
            "language": data["language"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=404, detail=f"Erro ao buscar repositório: {str(e)}")

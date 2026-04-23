from fastapi import APIRouter, Depends
from .dependencies import get_git_mining_service
from .service import GitMiningService

router = APIRouter()


@router.get("/report")
async def generate_report(
    repo_url: str,
    service: GitMiningService = Depends(get_git_mining_service)
):
    data = service.process_gitlog(repo_url)
    return {
        "status": "success",
        "repo_analyzed": repo_url,
        "total_commits": len(data),
        "data": data
    }

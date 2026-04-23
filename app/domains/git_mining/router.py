from fastapi import APIRouter, Depends
from .dependencies import get_git_mining_service
from .service import GitMiningService

router = APIRouter()


@router.get("/report")
async def generate_report(
    repo_url: str,
    service: GitMiningService = Depends(get_git_mining_service)
):
    d3_data = service.get_d3_hierarchical_data(repo_url)

    return {
        "status": "success",
        "repo_analyzed": repo_url,
        "d3_data": d3_data
    }

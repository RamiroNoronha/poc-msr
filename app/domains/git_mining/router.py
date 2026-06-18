from typing import Optional

from fastapi import APIRouter, Depends
from .dependencies import get_git_mining_service
from .service import GitMiningService

router = APIRouter()


@router.get("/report")
async def generate_report(
    repo_url: str,
    branch: Optional[str] = None,
    service: GitMiningService = Depends(get_git_mining_service)
):
    d3_data = service.get_d3_hierarchical_data(repo_url, branch)

    return {
        "status": "success",
        "repo_analyzed": repo_url,
        "d3_data": d3_data
    }


@router.get("/report/author")
async def generate_author_report(
    repo_url: str,
    author: str,
    branch: Optional[str] = None,
    service: GitMiningService = Depends(get_git_mining_service)
):
    d3_data = service.get_author_d3_hierarchical_data(repo_url, author, branch)

    return {
        "status": "success",
        "repo_analyzed": repo_url,
        "author_filter": author,
        "d3_data": d3_data
    }

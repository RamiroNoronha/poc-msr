from typing import Optional

from fastapi import APIRouter, Depends, Query
from .dependencies import get_coupling_service
from .service import CouplingService

router = APIRouter()


@router.get("/report/coupling")
async def generate_coupling_report(
    repo_url: str,
    branch: Optional[str] = None,
    months: Optional[int] = Query(None, ge=1, le=240),
    min_support: int = Query(3, ge=1, le=100),
    limit: int = Query(300, ge=1, le=1000),
    service: CouplingService = Depends(get_coupling_service)
):
    """
    Historical (change) coupling between files: files that change together in the same commits.

    Args:
        repo_url: Repository location.
        branch: Optional branch.
        months: Only commits within this many months before the repository's latest commit.
        min_support: Minimum number of commits in which both files changed.
        limit: Maximum number of file pairs returned (strongest first).
    """
    return {
        "status": "success",
        "repo_analyzed": repo_url,
        **service.get_coupling_report(repo_url, branch, months, min_support, limit)
    }

from typing import Optional
from .dependencies import get_truck_factor_service
from fastapi import APIRouter, Depends
from app.domains.git_mining.schemas import AnalysisRequest
from .service import TruckFactorService

router = APIRouter()


@router.get("/report/truck-factor")
async def generate_truck_factor_report(
    repo_url: str,
    branch: Optional[str] = None,
    service: TruckFactorService = Depends(get_truck_factor_service)
):
    """
    Endpoint mapping socio-technical analytics reports for system repositories.

    Args:
        repo_url: Repository cloud location.
        branch: Version branch string context filter.
        service: Injected analytic processing engine interface.

    Returns:
        The simulated payload results object.
    """
    return service.get_truck_factor_report(repo_url, branch)


@router.post("/report/truck-factor")
async def generate_truck_factor_report_with_groups(
    request: AnalysisRequest,
    service: TruckFactorService = Depends(get_truck_factor_service)
):
    """Same as the GET report, using identity groups confirmed by the user."""
    return service.get_truck_factor_report(request.repo_url, request.branch, request.groups)

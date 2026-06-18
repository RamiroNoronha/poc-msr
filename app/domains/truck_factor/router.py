from typing import Optional
from .dependencies import get_truck_factor_service
from fastapi import APIRouter, Depends
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

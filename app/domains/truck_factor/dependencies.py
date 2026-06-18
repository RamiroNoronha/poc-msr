from fastapi import Depends
from app.domains.git_mining.dependencies import get_git_mining_service
from app.domains.git_mining.service import GitMiningService
from .service import TruckFactorService


def get_truck_factor_service(
    git_mining_service: GitMiningService = Depends(get_git_mining_service)
) -> TruckFactorService:
    return TruckFactorService(git_mining_service)

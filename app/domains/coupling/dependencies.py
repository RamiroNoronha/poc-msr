from fastapi import Depends
from app.domains.git_mining.dependencies import get_git_mining_service
from app.domains.git_mining.service import GitMiningService
from .service import CouplingService


def get_coupling_service(
    git_mining_service: GitMiningService = Depends(get_git_mining_service)
) -> CouplingService:
    return CouplingService(git_mining_service)

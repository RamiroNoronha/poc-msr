from fastapi import Depends
from .infrastructure.git_miner import NativeGitMiner
from .service import GitMiningService
from .contracts import GitMinerProtocol


def get_git_miner() -> GitMinerProtocol:
    return NativeGitMiner()


def get_git_mining_service(
    miner: GitMinerProtocol = Depends(get_git_miner)
) -> GitMiningService:
    return GitMiningService(miner)

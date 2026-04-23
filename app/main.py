import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.v1.github import router as github_router
from app.domains.git_mining.router import router as git_mining_router
from app.core.config import settings

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("📄 Swagger UI:  http://localhost:8000/docs")
    logger.info("📘 ReDoc:       http://localhost:8000/redoc")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

app.include_router(github_router, prefix=settings.API_V1_STR, tags=["github"])

app.include_router(
    git_mining_router,
    prefix=f"{settings.API_V1_STR}/mining",
    tags=["git-mining"]
)


@app.get("/", tags=["health"])
def read_root():
    return {"status": "online", "project": settings.PROJECT_NAME}

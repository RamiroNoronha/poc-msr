import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.domains.git_mining.repository_guard import RepositoryRejected
from app.api.v1.github import router as github_router
from app.domains.coupling.router import router as coupling_router
from app.domains.git_mining.router import router as git_mining_router
from app.domains.truck_factor.router import router as truck_factor_router
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

@app.exception_handler(RepositoryRejected)
async def repository_rejected_handler(_: Request, error: RepositoryRejected):
    # O front mostra o `detail` como veio.
    return JSONResponse(status_code=error.status_code, content={"detail": error.message})


app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",")],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(github_router, prefix=settings.API_V1_STR, tags=["github"])

app.include_router(
    git_mining_router,
    prefix=f"{settings.API_V1_STR}/mining",
    tags=["git-mining"]
)

app.include_router(
    truck_factor_router,
    prefix=f"{settings.API_V1_STR}/analytics",
    tags=["truck-factor"]
)

app.include_router(
    coupling_router,
    prefix=f"{settings.API_V1_STR}/analytics",
    tags=["coupling"]
)

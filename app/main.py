from fastapi import FastAPI
from app.api.v1.github import router as github_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.include_router(github_router, prefix=settings.API_V1_STR, tags=["github"])


@app.get("/", tags=["health"])
def read_root():
    return {"status": "online", "project": settings.PROJECT_NAME}

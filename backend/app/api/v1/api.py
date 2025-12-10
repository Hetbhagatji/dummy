from app.api.v1.endpoints import resume
from fastapi import APIRouter
from app.api.v1.endpoints import job
api_router = APIRouter()

api_router.include_router(
    resume.router,
    prefix="/resume",
    tags=["Resume"]
)
api_router.include_router(
    job.router,
    prefix="/job",
    tags=["Job"]
)

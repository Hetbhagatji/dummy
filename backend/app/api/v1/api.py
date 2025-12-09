from app.api.v1.endpoints import resume
from fastapi import APIRouter

api_router = APIRouter()

api_router.include_router(
    resume.router,
    prefix="/resume",
    tags=["Resume"]
)

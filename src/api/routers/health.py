from fastapi import APIRouter

from src.api.schemas import HealthResponse


router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(status="ok", service="learning-os-api")

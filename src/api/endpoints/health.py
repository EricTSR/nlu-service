from fastapi import APIRouter, status

from src.schemas.health import HealthCheck

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    response_model=HealthCheck,
    status_code=status.HTTP_200_OK,
)
def get_health() -> HealthCheck:
    return HealthCheck()

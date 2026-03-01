from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_cache_service, get_chroma_client, get_math_client, get_viet_client
from app.models.schemas import HealthResponse
from app.services.health_service import HealthService

router = APIRouter(prefix="/api/v1/health", tags=["health"])


def _health_service() -> HealthService:
    return HealthService(
        chroma_client=get_chroma_client(),
        math_client=get_math_client(),
        viet_client=get_viet_client(),
        cache_service=get_cache_service(),
    )


@router.get("/live", response_model=HealthResponse)
async def live(service: HealthService = Depends(_health_service)):
    data = await service.live()
    return HealthResponse(status=data["status"])


@router.get("/ready", response_model=HealthResponse)
async def ready(service: HealthService = Depends(_health_service)):
    ok, details = await service.ready()
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "degraded", "details": details},
        )
    return HealthResponse(status="ok", details=details)

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse

from app.config.logging import configure_logging
from app.config.metrics import metrics_payload
from app.config.settings import get_settings
from app.dependencies import get_cache_service, get_math_client, get_viet_client
from app.middleware.request_context import RequestContextMiddleware
from app.routers.health import router as health_router
from app.routers.workflow import router as workflow_router

configure_logging()
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await get_math_client().aclose()
    await get_viet_client().aclose()
    await get_cache_service().aclose()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(RequestContextMiddleware)
app.include_router(workflow_router)
app.include_router(health_router)


@app.get("/metrics")
async def metrics() -> Response:
    payload, content_type = metrics_payload()
    return Response(content=payload, media_type=content_type)


@app.get("/")
async def root() -> JSONResponse:
    return JSONResponse({"service": settings.app_name, "version": settings.app_version})

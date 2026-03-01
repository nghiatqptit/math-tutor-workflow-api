from __future__ import annotations

import logging
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.config.metrics import REQUEST_COUNT, REQUEST_LATENCY

logger = logging.getLogger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        request.state.request_id = request_id
        start = time.perf_counter()
        path = request.url.path
        method = request.method

        try:
            response: Response = await call_next(request)
            status_code = str(response.status_code)
        except Exception:
            elapsed = time.perf_counter() - start
            REQUEST_COUNT.labels(path=path, method=method, status="500").inc()
            REQUEST_LATENCY.labels(path=path, method=method).observe(elapsed)
            logger.exception(
                "request_failed",
                extra={"request_id": request_id},
            )
            raise

        elapsed = time.perf_counter() - start
        REQUEST_COUNT.labels(path=path, method=method, status=status_code).inc()
        REQUEST_LATENCY.labels(path=path, method=method).observe(elapsed)
        response.headers["x-request-id"] = request_id

        logger.info(
            "request_complete",
            extra={"request_id": request_id},
        )
        return response

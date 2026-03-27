"""Middleware stack — Observability, Rate Limiting, Upload Validation."""
import uuid
import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Adds request ID, logs method/path/duration for every request."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        start = time.time()
        response = await call_next(request)
        duration_ms = round((time.time() - start) * 1000)

        # Skip noisy paths
        path = request.url.path
        if path not in ("/api/health", "/favicon.ico"):
            logger.info(
                f"[{request_id}] {request.method} {path} -> {response.status_code} ({duration_ms}ms)"
            )

        response.headers["X-Request-Id"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms}ms"
        return response


class UploadSizeMiddleware(BaseHTTPMiddleware):
    """Reject oversized uploads early (before processing)."""

    MAX_BODY_SIZE = 100 * 1024 * 1024  # 100MB default

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.MAX_BODY_SIZE:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=413,
                content={"error": {"code": "upload_too_large", "message": f"Max upload size is {self.MAX_BODY_SIZE // (1024*1024)}MB"}},
            )
        return await call_next(request)

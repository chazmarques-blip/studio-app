"""Standardized error taxonomy (Stripe-style).
All API errors follow a consistent format for frontend consumption.
"""
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base application error with structured response."""

    def __init__(self, code: str, message: str, status: int = 400, details: dict = None):
        self.code = code
        self.message = message
        self.status = status
        self.details = details or {}
        super().__init__(message)


class ValidationError(AppError):
    def __init__(self, field: str, message: str):
        super().__init__(code="validation_error", message=message, status=422, details={"field": field})


class NotFoundError(AppError):
    def __init__(self, resource: str, resource_id: str = ""):
        msg = f"{resource} not found" if not resource_id else f"{resource} '{resource_id}' not found"
        super().__init__(code="not_found", message=msg, status=404)


class ProviderError(AppError):
    def __init__(self, provider: str, message: str, retry_after: int = None):
        details = {"provider": provider}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(code="provider_error", message=f"{provider}: {message}", status=502, details=details)


class RateLimitError(AppError):
    def __init__(self, limit: str, retry_after: int = 60):
        super().__init__(
            code="rate_limit_exceeded",
            message=f"Rate limit exceeded: {limit}",
            status=429,
            details={"retry_after": retry_after},
        )


class AuthenticationError(AppError):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(code="auth_error", message=message, status=401)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Access denied"):
        super().__init__(code="forbidden", message=message, status=403)


class UploadTooLargeError(AppError):
    def __init__(self, max_size_mb: int):
        super().__init__(
            code="upload_too_large",
            message=f"File exceeds maximum size of {max_size_mb}MB",
            status=413,
            details={"max_size_mb": max_size_mb},
        )


# ── Exception Handlers (register in server.py) ──

async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handle all AppError subclasses with consistent JSON format."""
    logger.warning(f"AppError [{exc.code}]: {exc.message} | path={request.url.path}")
    return JSONResponse(
        status_code=exc.status,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unhandled exceptions."""
    logger.error(f"Unhandled error: {exc} | path={request.url.path}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "internal_error", "message": "An unexpected error occurred", "details": {}}},
    )

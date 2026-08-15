"""Centralised exception-to-JSON error handling.

All error responses use the documented envelope:
``{"error": {"code": "...", "message": "...", "details": {}}}``.
Messages never contain stack traces, paths, environment values, or internal
details (SEC-046).
"""

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ..core.exceptions import ApiError

logger = logging.getLogger(__name__)


def error_response(
    code: str, message: str, details: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Build the standard error envelope."""
    return {"error": {"code": code, "message": message, "details": details or {}}}


def register_error_handlers(app: FastAPI) -> None:
    """Attach the application's error handlers to the FastAPI app."""
    register_exception_handler(app)
    register_request_validation_handler(app)


def register_exception_handler(app: FastAPI) -> None:
    """Handle :class:`ApiError` and unexpected exceptions."""

    @app.exception_handler(ApiError)
    async def handle_api_error(_request: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(code=exc.code, message=exc.message),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(_request: Request, exc: Exception) -> JSONResponse:
        # Log the real exception server-side, but never leak details to clients.
        logger.exception("Unhandled exception during request", exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                code="internal_error",
                message="An unexpected error occurred. Please try again later.",
            ),
        )


def register_request_validation_handler(app: FastAPI) -> None:
    """Convert 422 validation errors into the standard error envelope."""

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = {}
        for error in exc.errors():
            location = error.get("loc", ())
            field = str(location[-1]) if location else "body"
            details[field] = error.get("msg", "Invalid value")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=error_response(
                code="validation_error",
                message="Request validation failed.",
                details=details,
            ),
        )

"""
Error handling middleware.
"""

import logging
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from api.errors.base_error import ServiceError

# Create logger
logger = logging.getLogger(__name__)


class ServiceErrorMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle ServiceError exceptions.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and handle ServiceError exceptions.

        Args:
            request: Request object
            call_next: Next middleware or endpoint

        Returns:
            Response: Response object
        """
        try:
            return await call_next(request)
        except ServiceError as e:
            # Log error
            logger.warning(
                f"ServiceError: {e.code} - {e.reason}",
                extra={
                    "code": e.code,
                    "reason": e.reason,
                    "description": e.description,
                    "details": e.details,
                    "path": request.url.path,
                    "method": request.method,
                },
            )

            # Return error response
            return JSONResponse(
                status_code=400,
                content={"code": e.code, "message": e.reason, "details": e.details},
            )
        except Exception as e:
            # Log unexpected error
            logger.exception(
                f"Unexpected error: {str(e)}",
                extra={"path": request.url.path, "method": request.method},
            )

            # Return error response
            return JSONResponse(
                status_code=500,
                content={
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "Internal server error",
                    "details": {"error": str(e)} if request.app.debug else {},
                },
            )

"""
Error handling middleware.
"""

import logging
import time
from typing import Callable, Dict, Any

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from api.config import get_config
from api.errors.base_error import ServiceError

# Create logger
logger = logging.getLogger(__name__)

# Get configuration
config = get_config()


class ServiceErrorMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle ServiceError exceptions and monitor performance.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request, monitor performance, and handle exceptions.

        Args:
            request: Request object
            call_next: Next middleware or endpoint

        Returns:
            Response: Response object
        """
        # Record start time for performance monitoring
        start_time = time.time()

        # Extract request information for logging
        request_id = request.headers.get("X-Request-ID", "")
        user_agent = request.headers.get("User-Agent", "")
        client_ip = request.client.host if request.client else ""

        # Prepare log context
        log_context = {
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "client_ip": client_ip,
            "user_agent": user_agent,
        }

        try:
            # Process the request
            response = await call_next(request)

            # Calculate request processing time
            process_time = time.time() - start_time

            # Add processing time header to response
            response.headers["X-Process-Time"] = str(process_time)

            # Log slow requests
            if process_time > 1.0:  # Log requests taking more than 1 second
                logger.warning(
                    f"Slow request: {request.method} {request.url.path} took {process_time:.4f}s",
                    extra={**log_context, "process_time": process_time},
                )

            return response

        except ServiceError as e:
            # Calculate error processing time
            process_time = time.time() - start_time

            # Enhance log context with error details
            error_context = {
                **log_context,
                "process_time": process_time,
                "error_code": e.code,
                "error_reason": e.reason,
                "error_description": e.description,
                "error_details": e.details,
            }

            # Log service error
            logger.warning(f"ServiceError: {e.code} - {e.reason}", extra=error_context)

            # Return error response
            return JSONResponse(
                status_code=400,
                content={
                    "code": e.code,
                    "message": e.reason,
                    "details": e.details,
                    "request_id": request_id,
                },
                headers={"X-Process-Time": str(process_time)},
            )

        except Exception as e:
            # Calculate error processing time
            process_time = time.time() - start_time

            # Enhance log context with error details
            error_context = {
                **log_context,
                "process_time": process_time,
                "error_type": type(e).__name__,
                "error_message": str(e),
            }

            # Log unexpected error
            logger.exception(f"Unexpected error: {str(e)}", extra=error_context)

            # Prepare error details
            error_details: Dict[str, Any] = {}
            if config.debug:
                error_details = {"error": str(e), "error_type": type(e).__name__}

            # Return error response
            return JSONResponse(
                status_code=500,
                content={
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "Internal server error",
                    "details": error_details,
                    "request_id": request_id,
                },
                headers={"X-Process-Time": str(process_time)},
            )

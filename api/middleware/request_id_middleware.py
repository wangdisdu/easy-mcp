"""
Request ID middleware.
"""

import logging
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Create logger
logger = logging.getLogger(__name__)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add request ID to each request.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and add request ID.

        Args:
            request: Request object
            call_next: Next middleware or endpoint

        Returns:
            Response: Response object
        """
        # Check if request already has an ID
        request_id = request.headers.get("X-Request-ID")

        # Generate a new request ID if not present
        if not request_id:
            request_id = str(uuid.uuid4())

        # Add request ID to request state
        request.state.request_id = request_id

        # Process the request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response

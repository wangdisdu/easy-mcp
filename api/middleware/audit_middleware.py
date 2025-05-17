"""
Audit middleware.
"""

import json
import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from api.database import get_session
from api.models.tb_audit import TbAudit
from api.utils.time_util import get_current_unix_ms

# Create logger
logger = logging.getLogger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware to audit HTTP requests.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and audit it.

        Args:
            request: Request object
            call_next: Next middleware or endpoint

        Returns:
            Response: Response object
        """
        # Skip audit for some paths
        if (
            request.url.path.startswith("/docs")
            or request.url.path.startswith("/openapi")
            or request.url.path.startswith("/redoc")
        ):
            return await call_next(request)

        # Get request information
        method = request.method
        path = request.url.path
        client_host = request.client.host if request.client else None

        # Process request
        response = await call_next(request)

        # Skip audit for GET requests
        if method == "GET":
            return response

        # Get user from request state if available
        username = "anonymous"
        user_id = None
        if hasattr(request.state, "user"):
            username = request.state.user.username
            user_id = request.state.user.id

        # Determine resource type and action
        resource_type = "unknown"
        action = "unknown"
        resource_id = None
        resource_name = None

        # Parse path to determine resource type and action
        parts = path.strip("/").split("/")
        if len(parts) >= 2 and parts[0] == "api" and parts[1] == "v1":
            if len(parts) >= 3:
                resource_type = parts[2]

                if method == "POST":
                    action = "create"
                    if len(parts) >= 4 and parts[3] == "deploy":
                        action = "deploy"
                elif method == "PUT":
                    action = "update"
                    if len(parts) >= 5 and parts[4] == "deploy":
                        action = "deploy"
                elif method == "DELETE":
                    action = "delete"

                if len(parts) >= 4 and parts[3].isdigit():
                    resource_id = int(parts[3])

        # Create audit log
        try:
            async with get_session() as db:
                audit_log = TbAudit(
                    user_id=user_id,
                    username=username,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    resource_name=resource_name,
                    details=json.dumps(
                        {
                            "method": method,
                            "path": path,
                            "status_code": response.status_code,
                        }
                    ),
                    ip_address=client_host,
                    created_at=get_current_unix_ms(),
                )

                db.add(audit_log)
                await db.commit()
        except Exception as e:
            logger.exception(f"Error creating audit log: {str(e)}")

        return response

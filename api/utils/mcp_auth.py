"""
Authentication for MCP transport endpoints.

The MCP SSE / Streamable HTTP endpoints are machine-facing and cannot perform
interactive login, so they authenticate with a long-lived bearer token managed
in the database (see api.models.tb_token). Each token is scoped to an explicit
set of tools.

Authentication is fail-open when unconfigured: if no tokens exist at all, the
MCP endpoints run open (unauthenticated, all enabled tools) for backward
compatibility. As soon as at least one token exists, authentication is
enforced — every request must present a valid token, otherwise it is rejected
with 401. To turn authentication back off, delete all tokens. Tokens cannot
be disabled; deletion is the only way to revoke one.

A token with no associated tools can authenticate but is authorized for no
tools.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

from fastapi import Depends, Request, status
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.services.token_service import TokenService

logger = logging.getLogger(__name__)

_UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Missing or invalid MCP access token",
    headers={"WWW-Authenticate": "Bearer"},
)


@dataclass
class McpAuthScope:
    """Resolved authorization scope for an authenticated MCP request."""

    token_id: int
    token_name: str
    # Tool IDs this token may list/execute. Empty list means no tools;
    # None means no restriction (unauthenticated open mode).
    allowed_tool_ids: Optional[List[int]]


def _extract_token(request: Request) -> Optional[str]:
    """
    Extract the bearer token from the request.

    Order: ``Authorization: Bearer <token>`` header, then ``?token=`` query
    parameter (fallback for clients that cannot set custom headers).
    """
    auth = request.headers.get("authorization")
    if auth:
        parts = auth.split(" ", 1)
        if len(parts) == 2 and parts[0].lower() == "bearer" and parts[1].strip():
            return parts[1].strip()

    qp = request.query_params.get("token")
    if qp and qp.strip():
        return qp.strip()

    return None


async def verify_mcp_token(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> McpAuthScope:
    """
    FastAPI dependency that authenticates an MCP request.

    Raises:
        HTTPException: 401 if tokens are configured and no valid token is
            presented.
    """
    service = TokenService(db)

    # Fail-open when unconfigured: no tokens at all => run open.
    if await service.count_tokens() == 0:
        return McpAuthScope(
            token_id=0,
            token_name="(unauthenticated)",
            allowed_tool_ids=None,  # None => no tool restriction
        )

    raw = _extract_token(request)
    if not raw:
        logger.warning("MCP request rejected: no token presented")
        raise _UNAUTHORIZED

    token = await service.get_token_by_value(raw)
    if not token:
        logger.warning("MCP request rejected: unknown or disabled token")
        raise _UNAUTHORIZED

    tool_ids = await service.get_tool_ids_for_token(token.id)
    return McpAuthScope(
        token_id=token.id,
        token_name=token.name,
        allowed_tool_ids=tool_ids,
    )

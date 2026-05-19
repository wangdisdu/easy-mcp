"""
Token router.

Admin-protected management API for MCP access tokens. The MCP transport
endpoints themselves are guarded by api.utils.mcp_auth, not this router.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models.tb_token import TbToken
from api.models.tb_user import TbUser
from api.schemas.common_schema import PaginatedResponse, Response
from api.schemas.token_schema import (
    TokenCreate,
    TokenUpdate,
    TokenResponse,
)
from api.services.token_service import TokenService
from api.utils.security_util import get_current_user

# Create router
router = APIRouter(prefix="/token", tags=["token"])


def _to_response(token: TbToken, tool_ids: list) -> TokenResponse:
    """Build a TokenResponse from a token model and its tool IDs."""
    return TokenResponse.model_validate(
        {
            "id": token.id,
            "name": token.name,
            "description": token.description,
            "token": token.token,
            "tool_ids": tool_ids,
            "created_at": token.created_at,
            "updated_at": token.updated_at,
            "created_by": token.created_by,
            "updated_by": token.updated_by,
        }
    )


@router.get("", response_model=PaginatedResponse[TokenResponse])
async def get_tokens(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=1000, description="Page size"),
    search: Optional[str] = Query(
        None, description="Search term for name or description"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Get tokens with pagination.

    Returns:
        PaginatedResponse[TokenResponse]: Paginated list of tokens
    """
    service = TokenService(db)
    tokens, total = await service.query_tokens(page, size, search)

    data = []
    for token in tokens:
        tool_ids = await service.get_tool_ids_for_token(token.id)
        data.append(_to_response(token, tool_ids))

    return PaginatedResponse(data=data, total=total)


@router.post("", response_model=Response[TokenResponse])
async def create_token(
    token_data: TokenCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Create a new token.

    Returns:
        Response[TokenResponse]: Created token (includes the secret value)
    """
    service = TokenService(db)
    token, tool_ids = await service.create_token(token_data, current_user.username)

    return Response(data=_to_response(token, tool_ids))


@router.get("/{token_id}", response_model=Response[TokenResponse])
async def get_token(
    token_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Get token by ID.

    Returns:
        Response[TokenResponse]: Token details
    """
    service = TokenService(db)
    token = await service.get_token_by_id(token_id)

    if not token:
        from api.errors.token_error import TokenNotFoundError

        raise TokenNotFoundError(token_id=token_id)

    tool_ids = await service.get_tool_ids_for_token(token.id)
    return Response(data=_to_response(token, tool_ids))


@router.put("/{token_id}", response_model=Response[TokenResponse])
async def update_token(
    token_id: int,
    token_data: TokenUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Update a token (name, description, or tool bindings).

    Returns:
        Response[TokenResponse]: Updated token
    """
    service = TokenService(db)
    token, tool_ids = await service.update_token(
        token_id, token_data, current_user.username
    )

    return Response(data=_to_response(token, tool_ids))


@router.delete("/{token_id}", response_model=Response[None])
async def delete_token(
    token_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Delete a token.

    Returns:
        Response[None]: Success response
    """
    service = TokenService(db)
    await service.delete_token(token_id, current_user.username)

    return Response(data=None, message="Token deleted successfully")

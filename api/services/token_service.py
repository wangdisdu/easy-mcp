"""
Token service.

Manages MCP access tokens and their tool associations. Tokens authenticate
the MCP transport endpoints; the associated tools scope what a token may
list and execute.
"""

import logging
import secrets
from typing import List, Optional, Tuple

from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from api.errors.token_error import TokenNotFoundError, TokenAlreadyExistsError
from api.models.tb_token import TbToken, TbTokenTool
from api.schemas.token_schema import TokenCreate, TokenUpdate
from api.utils.audit_util import _create_audit_log
from api.utils.time_util import get_current_unix_ms

# Get logger
logger = logging.getLogger(__name__)

TOKEN_PREFIX = "emcp_"


def _generate_token() -> str:
    """Generate a new opaque bearer token."""
    return TOKEN_PREFIX + secrets.token_urlsafe(32)


class TokenService:
    """Token service class."""

    def __init__(self, db: AsyncSession):
        """
        Initialize token service.

        Args:
            db: Database session
        """
        self.db = db

    async def get_token_by_id(self, token_id: int) -> Optional[TbToken]:
        """Get token by ID."""
        result = await self.db.execute(select(TbToken).where(TbToken.id == token_id))
        return result.scalars().first()

    async def get_token_by_name(self, name: str) -> Optional[TbToken]:
        """Get token by name."""
        result = await self.db.execute(select(TbToken).where(TbToken.name == name))
        return result.scalars().first()

    async def get_token_by_value(self, token: str) -> Optional[TbToken]:
        """
        Get a token by its secret value.

        Used by the MCP auth dependency.

        Args:
            token: Token secret value

        Returns:
            Optional[TbToken]: Token if found, None otherwise
        """
        if not token:
            return None
        result = await self.db.execute(select(TbToken).where(TbToken.token == token))
        return result.scalars().first()

    async def count_tokens(self) -> int:
        """
        Count all tokens.

        Used to decide whether MCP authentication is active: if no tokens
        exist at all, the MCP endpoints run open (backward compatible).
        """
        result = await self.db.execute(select(func.count(TbToken.id)))
        return result.scalar() or 0

    async def get_tool_ids_for_token(self, token_id: int) -> List[int]:
        """
        Get the list of tool IDs a token is allowed to access.

        Args:
            token_id: Token ID

        Returns:
            List[int]: Associated tool IDs (empty list means no tools)
        """
        result = await self.db.execute(
            select(TbTokenTool.tool_id).where(TbTokenTool.token_id == token_id)
        )
        return [row[0] for row in result.all()]

    async def _set_token_tools(
        self, token_id: int, tool_ids: List[int], current_user: str
    ) -> None:
        """
        Replace the set of tools associated with a token.

        Args:
            token_id: Token ID
            tool_ids: Tool IDs to associate
            current_user: Current user
        """
        # Remove existing associations
        await self.db.execute(
            TbTokenTool.__table__.delete().where(TbTokenTool.token_id == token_id)
        )

        # Insert new associations (de-duplicated)
        current_time = get_current_unix_ms()
        for tool_id in sorted(set(tool_ids)):
            self.db.add(
                TbTokenTool(
                    token_id=token_id,
                    tool_id=tool_id,
                    created_at=current_time,
                    created_by=current_user,
                )
            )

    async def create_token(
        self, token_data: TokenCreate, current_user: str
    ) -> Tuple[TbToken, List[int]]:
        """
        Create a new token.

        Args:
            token_data: Token data
            current_user: Current user

        Returns:
            Tuple[TbToken, List[int]]: Created token and associated tool IDs

        Raises:
            TokenAlreadyExistsError: If a token with the same name exists
        """
        existing = await self.get_token_by_name(token_data.name)
        if existing:
            raise TokenAlreadyExistsError(name=token_data.name)

        current_time = get_current_unix_ms()
        token = TbToken(
            name=token_data.name,
            description=token_data.description,
            token=_generate_token(),
            created_at=current_time,
            updated_at=current_time,
            created_by=current_user,
            updated_by=current_user,
        )

        self.db.add(token)
        await self.db.commit()
        await self.db.refresh(token)

        await self._set_token_tools(token.id, token_data.tool_ids, current_user)
        await self.db.commit()

        await _create_audit_log(
            self.db,
            current_user,
            "create",
            "token",
            token.id,
            token.name,
            {
                "name": token.name,
                "description": token.description,
                "tool_ids": sorted(set(token_data.tool_ids)),
            },
            None,
        )

        logger.info(f"Token created: {token.name} by {current_user}")
        return token, sorted(set(token_data.tool_ids))

    async def query_tokens(
        self, page: int = 1, size: int = 20, search: Optional[str] = None
    ) -> Tuple[List[TbToken], int]:
        """
        Query tokens with pagination.

        Args:
            page: Page number (1-based)
            size: Page size
            search: Search term for name or description

        Returns:
            Tuple[List[TbToken], int]: List of tokens and total count
        """
        query = select(TbToken)
        count_query = select(func.count(TbToken.id))

        if search:
            condition = or_(
                TbToken.name.ilike(f"%{search}%"),
                TbToken.description.ilike(f"%{search}%"),
            )
            query = query.where(condition)
            count_query = count_query.where(condition)

        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        query = query.order_by(TbToken.name).offset((page - 1) * size).limit(size)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def update_token(
        self, token_id: int, token_data: TokenUpdate, current_user: str
    ) -> Tuple[TbToken, List[int]]:
        """
        Update a token.

        Args:
            token_id: Token ID
            token_data: Token update data
            current_user: Current user

        Returns:
            Tuple[TbToken, List[int]]: Updated token and associated tool IDs

        Raises:
            TokenNotFoundError: If token not found
            TokenAlreadyExistsError: If renamed to an existing token name
        """
        token = await self.get_token_by_id(token_id)
        if not token:
            raise TokenNotFoundError(token_id=token_id)

        if token_data.name and token_data.name != token.name:
            existing = await self.get_token_by_name(token_data.name)
            if existing:
                raise TokenAlreadyExistsError(name=token_data.name)

        old_values = {
            "name": token.name,
            "description": token.description,
        }

        if token_data.name is not None:
            token.name = token_data.name
        if token_data.description is not None:
            token.description = token_data.description

        token.updated_at = get_current_unix_ms()
        token.updated_by = current_user

        if token_data.tool_ids is not None:
            await self._set_token_tools(token_id, token_data.tool_ids, current_user)

        await self.db.commit()
        await self.db.refresh(token)

        tool_ids = await self.get_tool_ids_for_token(token_id)

        await _create_audit_log(
            self.db,
            current_user,
            "update",
            "token",
            token.id,
            token.name,
            {
                "old": old_values,
                "new": {
                    "name": token.name,
                    "description": token.description,
                    "tool_ids": tool_ids,
                },
            },
            None,
        )

        logger.info(f"Token updated: {token.name} by {current_user}")
        return token, tool_ids

    async def delete_token(self, token_id: int, current_user: str) -> None:
        """
        Delete a token and its tool associations.

        Args:
            token_id: Token ID
            current_user: Current user

        Raises:
            TokenNotFoundError: If token not found
        """
        token = await self.get_token_by_id(token_id)
        if not token:
            raise TokenNotFoundError(token_id=token_id)

        token_info = {"name": token.name, "description": token.description}

        await self.db.execute(
            TbTokenTool.__table__.delete().where(TbTokenTool.token_id == token_id)
        )
        await self.db.delete(token)
        await self.db.commit()

        await _create_audit_log(
            self.db,
            current_user,
            "delete",
            "token",
            token_id,
            token_info["name"],
            token_info,
            None,
        )

        logger.info(f"Token deleted: {token_info['name']} by {current_user}")

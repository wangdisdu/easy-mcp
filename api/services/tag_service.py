"""
Tag service.
"""

import logging
from typing import List, Optional, Tuple

from sqlalchemy import func, select, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from api.errors.tag_error import TagNotFoundError, TagAlreadyExistsError
from api.models.tb_tag import TbTag, TbToolTag
from api.schemas.tag_schema import TagCreate, TagUpdate
from api.utils.audit_util import audit, _create_audit_log
from api.utils.time_util import get_current_unix_ms

# Get logger
logger = logging.getLogger(__name__)


class TagService:
    """Tag service class."""

    def __init__(self, db: AsyncSession):
        """
        Initialize tag service.

        Args:
            db: Database session
        """
        self.db = db

    async def create_tag(self, tag_data: TagCreate, current_user: str) -> TbTag:
        """
        Create a new tag.

        Args:
            tag_data: Tag data
            current_user: Current user

        Returns:
            TbTag: Created tag

        Raises:
            TagAlreadyExistsError: If tag with the same name already exists
        """
        # Check if tag with the same name already exists
        existing_tag = await self.get_tag_by_name(tag_data.name)
        if existing_tag:
            raise TagAlreadyExistsError(name=tag_data.name)

        # Create tag
        current_time = get_current_unix_ms()
        tag = TbTag(
            name=tag_data.name,
            description=tag_data.description,
            created_at=current_time,
            updated_at=current_time,
            created_by=current_user,
            updated_by=current_user,
        )

        self.db.add(tag)
        await self.db.commit()
        await self.db.refresh(tag)

        # Audit log
        await _create_audit_log(
            self.db,
            current_user,
            "create",
            "tag",
            tag.id,
            tag.name,
            {"name": tag.name, "description": tag.description},
            None,
        )

        logger.info(f"Tag created: {tag.name} by {current_user}")
        return tag

    async def get_tag_by_id(self, tag_id: int) -> Optional[TbTag]:
        """
        Get tag by ID.

        Args:
            tag_id: Tag ID

        Returns:
            Optional[TbTag]: Tag if found, None otherwise
        """
        result = await self.db.execute(select(TbTag).where(TbTag.id == tag_id))
        return result.scalars().first()

    async def get_tag_by_name(self, name: str) -> Optional[TbTag]:
        """
        Get tag by name.

        Args:
            name: Tag name

        Returns:
            Optional[TbTag]: Tag if found, None otherwise
        """
        result = await self.db.execute(select(TbTag).where(TbTag.name == name))
        return result.scalars().first()

    async def query_tags(
        self, page: int = 1, size: int = 20, search: Optional[str] = None
    ) -> Tuple[List[TbTag], int]:
        """
        Query tags with pagination.

        Args:
            page: Page number (1-based)
            size: Page size
            search: Search term for name or description

        Returns:
            Tuple[List[TbTag], int]: List of tags and total count
        """
        query = select(TbTag)

        # Apply filters
        if search:
            query = query.where(
                or_(
                    TbTag.name.ilike(f"%{search}%"),
                    TbTag.description.ilike(f"%{search}%"),
                )
            )

        # Count total
        count_query = select(func.count(TbTag.id))

        # Apply the same filters to count query
        if search:
            count_query = count_query.where(
                or_(
                    TbTag.name.ilike(f"%{search}%"),
                    TbTag.description.ilike(f"%{search}%"),
                )
            )

        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # Apply pagination and ordering
        query = query.order_by(TbTag.name).offset((page - 1) * size).limit(size)

        result = await self.db.execute(query)
        tags = result.scalars().all()

        return list(tags), total

    async def update_tag(
        self, tag_id: int, tag_data: TagUpdate, current_user: str
    ) -> TbTag:
        """
        Update a tag.

        Args:
            tag_id: Tag ID
            tag_data: Tag update data
            current_user: Current user

        Returns:
            TbTag: Updated tag

        Raises:
            TagNotFoundError: If tag not found
            TagAlreadyExistsError: If tag with the same name already exists
        """
        # Get existing tag
        tag = await self.get_tag_by_id(tag_id)
        if not tag:
            raise TagNotFoundError(tag_id=tag_id)

        # Check if name is being changed and if new name already exists
        if tag_data.name and tag_data.name != tag.name:
            existing_tag = await self.get_tag_by_name(tag_data.name)
            if existing_tag:
                raise TagAlreadyExistsError(name=tag_data.name)

        # Store old values for audit
        old_values = {
            "name": tag.name,
            "description": tag.description,
        }

        # Update fields
        if tag_data.name is not None:
            tag.name = tag_data.name
        if tag_data.description is not None:
            tag.description = tag_data.description

        tag.updated_at = get_current_unix_ms()
        tag.updated_by = current_user

        await self.db.commit()
        await self.db.refresh(tag)

        # Audit log
        new_values = {
            "name": tag.name,
            "description": tag.description,
        }
        await _create_audit_log(
            self.db,
            current_user,
            "update",
            "tag",
            tag.id,
            tag.name,
            {"old": old_values, "new": new_values},
            None,
        )

        logger.info(f"Tag updated: {tag.name} by {current_user}")
        return tag

    async def delete_tag(self, tag_id: int, current_user: str) -> None:
        """
        Delete a tag.

        Args:
            tag_id: Tag ID
            current_user: Current user

        Raises:
            TagNotFoundError: If tag not found
        """
        # Get existing tag
        tag = await self.get_tag_by_id(tag_id)
        if not tag:
            raise TagNotFoundError(tag_id=tag_id)

        # Store tag info for audit
        tag_info = {
            "name": tag.name,
            "description": tag.description,
        }

        # Delete all tool-tag associations first
        await self.db.execute(
            TbToolTag.__table__.delete().where(TbToolTag.tag_id == tag_id)
        )

        # Delete tag
        await self.db.delete(tag)
        await self.db.commit()

        # Audit log
        await _create_audit_log(
            self.db,
            current_user,
            "delete",
            "tag",
            tag_id,
            tag_info["name"],
            tag_info,
            None,
        )

        logger.info(f"Tag deleted: {tag_info['name']} by {current_user}")

    async def get_tags_with_tool_count(
        self, page: int = 1, size: int = 20, search: Optional[str] = None
    ) -> Tuple[List[dict], int]:
        """
        Get tags with tool count.

        Args:
            page: Page number (1-based)
            size: Page size
            search: Search term for name or description

        Returns:
            Tuple[List[dict], int]: List of tags with tool count and total count
        """
        # Build base query with tool count
        query = (
            select(TbTag, func.count(TbToolTag.tool_id).label("tool_count"))
            .outerjoin(TbToolTag, TbTag.id == TbToolTag.tag_id)
            .group_by(TbTag.id)
        )

        # Apply filters
        if search:
            query = query.where(
                or_(
                    TbTag.name.ilike(f"%{search}%"),
                    TbTag.description.ilike(f"%{search}%"),
                )
            )

        # Count total (need to count distinct tags)
        count_query = select(func.count(func.distinct(TbTag.id)))
        if search:
            count_query = count_query.where(
                or_(
                    TbTag.name.ilike(f"%{search}%"),
                    TbTag.description.ilike(f"%{search}%"),
                )
            )

        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # Apply pagination and ordering
        query = query.order_by(TbTag.name).offset((page - 1) * size).limit(size)

        result = await self.db.execute(query)
        rows = result.all()

        # Convert to list of dictionaries
        tags_with_count = []
        for row in rows:
            tag = row[0]
            tool_count = row[1]
            tag_dict = {
                "id": tag.id,
                "name": tag.name,
                "description": tag.description,
                "tool_count": tool_count,
                "created_at": tag.created_at,
                "updated_at": tag.updated_at,
                "created_by": tag.created_by,
                "updated_by": tag.updated_by,
            }
            tags_with_count.append(tag_dict)

        return tags_with_count, total

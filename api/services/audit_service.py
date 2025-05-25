"""
Audit service.
"""

from typing import Optional, List, Tuple

from sqlalchemy import desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from api.models.tb_audit import TbAudit


class AuditService:
    """
    Audit service.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize audit service.

        Args:
            db: Database session
        """
        self.db = db

    async def query_audits(
        self,
        page: int = 1,
        size: int = 20,
        username: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        resource_name: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> Tuple[List[TbAudit], int]:
        """
        Query audit logs with pagination.

        Args:
            page: Page number (1-based)
            size: Page size
            username: Username filter
            action: Action filter
            resource_type: Resource type filter
            resource_id: Resource ID filter
            resource_name: Resource name filter
            start_time: Start time filter (UnixMS)
            end_time: End time filter (UnixMS)

        Returns:
            Tuple[List[TbAudit], int]: List of audit logs and total count
        """
        query = select(TbAudit)

        # Apply filters
        if username:
            query = query.where(TbAudit.username.ilike(f"%{username}%"))
        if action:
            query = query.where(TbAudit.action == action)
        if resource_type:
            query = query.where(TbAudit.resource_type == resource_type)
        if resource_id:
            query = query.where(TbAudit.resource_id == resource_id)
        if resource_name:
            query = query.where(TbAudit.resource_name.ilike(f"%{resource_name}%"))
        if start_time:
            query = query.where(TbAudit.created_at >= start_time)
        if end_time:
            query = query.where(TbAudit.created_at <= end_time)

        # Count total
        count_query = select(func.count(TbAudit.id))

        # Apply the same filters to count query
        if username:
            count_query = count_query.where(TbAudit.username.ilike(f"%{username}%"))
        if action:
            count_query = count_query.where(TbAudit.action == action)
        if resource_type:
            count_query = count_query.where(TbAudit.resource_type == resource_type)
        if resource_name:
            count_query = count_query.where(
                TbAudit.resource_name.ilike(f"%{resource_name}%")
            )
        if start_time:
            count_query = count_query.where(TbAudit.created_at >= start_time)
        if end_time:
            count_query = count_query.where(TbAudit.created_at <= end_time)

        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # Apply pagination and ordering
        query = (
            query.order_by(desc(TbAudit.created_at))
            .offset((page - 1) * size)
            .limit(size)
        )

        # Execute query
        result = await self.db.execute(query)
        audits = result.scalars().all()

        return list(audits), total

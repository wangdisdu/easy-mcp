"""
Audit router.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models.tb_user import TbUser
from api.schemas.audit_schema import AuditResponse
from api.schemas.common_schema import PaginatedResponse
from api.services.audit_service import AuditService
from api.utils.security_util import get_current_user

# Create router
router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=PaginatedResponse[AuditResponse])
async def get_audits(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    username: Optional[str] = Query(None, description="Username filter"),
    action: Optional[str] = Query(None, description="Action filter"),
    resource_type: Optional[str] = Query(None, description="Resource type filter"),
    resource_id: Optional[int] = Query(None, description="Resource ID filter"),
    resource_name: Optional[str] = Query(None, description="Resource name filter"),
    start_time: Optional[int] = Query(None, description="Start time filter (UnixMS)"),
    end_time: Optional[int] = Query(None, description="End time filter (UnixMS)"),
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Get audit logs with pagination.

    Args:
        page: Page number
        size: Page size
        username: Username filter
        action: Action filter
        resource_type: Resource type filter
        resource_id: Resource ID filter
        resource_name: Resource name filter
        start_time: Start time filter (UnixMS)
        end_time: End time filter (UnixMS)
        db: Database session
        current_user: Current user

    Returns:
        PaginatedResponse[AuditResponse]: Paginated list of audit logs
    """
    service = AuditService(db)
    audits, total = await service.query_audits(
        page,
        size,
        username,
        action,
        resource_type,
        resource_id,
        resource_name,
        start_time,
        end_time,
    )

    return PaginatedResponse(
        data=[AuditResponse.model_validate(audit) for audit in audits], total=total
    )

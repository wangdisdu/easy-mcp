"""
Tool log router.
"""

from typing import Optional, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models.tb_user import TbUser
from api.schemas.common_schema import PaginatedResponse, Response
from api.schemas.tool_log_schema import (
    ToolLogResponse,
    ToolStatsResponse,
    ToolTrendResponse,
    ToolUsageStatsResponse,
)
from api.services.tool_log_service import ToolLogService
from api.utils.security_util import get_current_user

# Create router
router = APIRouter(prefix="/tool-log", tags=["tool-log"])


@router.get("", response_model=PaginatedResponse[ToolLogResponse])
async def get_tool_logs(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    tool_name: Optional[str] = Query(None, description="Tool name filter"),
    call_type: Optional[str] = Query(None, description="Call type filter (mcp, debug)"),
    is_success: Optional[bool] = Query(None, description="Success status filter"),
    start_time: Optional[int] = Query(None, description="Start time filter (UnixMS)"),
    end_time: Optional[int] = Query(None, description="End time filter (UnixMS)"),
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Get tool logs with pagination.

    Args:
        page: Page number
        size: Page size
        tool_name: Tool name filter
        call_type: Call type filter (mcp, debug)
        is_success: Success status filter
        start_time: Start time filter (UnixMS)
        end_time: End time filter (UnixMS)
        db: Database session
        current_user: Current user

    Returns:
        PaginatedResponse[ToolLogResponse]: Paginated list of tool logs
    """
    service = ToolLogService(db)
    logs, total = await service.query_logs(
        page, size, tool_name, call_type, is_success, start_time, end_time
    )

    return PaginatedResponse(
        data=[ToolLogResponse.model_validate(log) for log in logs], total=total
    )


@router.get("/stats", response_model=Response[ToolStatsResponse])
async def get_tool_stats(
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Get tool statistics.

    Args:
        db: Database session
        current_user: Current user

    Returns:
        Response[ToolStatsResponse]: Tool statistics
    """
    service = ToolLogService(db)
    stats = await service.get_stats()

    return Response(data=stats)


@router.get("/trends", response_model=Response[List[ToolTrendResponse]])
async def get_tool_trends(
    days: int = Query(7, ge=1, le=30, description="Number of days"),
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Get tool trends.

    Args:
        days: Number of days
        db: Database session
        current_user: Current user

    Returns:
        Response[List[ToolTrendResponse]]: Tool trends
    """
    service = ToolLogService(db)
    trends = await service.get_trends(days)

    return Response(data=trends)


@router.get("/tool-stats", response_model=Response[List[ToolUsageStatsResponse]])
async def get_tool_usage_stats(
    limit: int = Query(10, ge=1, le=50, description="Number of tools"),
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Get tool usage statistics.

    Args:
        limit: Number of tools
        db: Database session
        current_user: Current user

    Returns:
        Response[List[ToolUsageStatsResponse]]: Tool usage statistics
    """
    service = ToolLogService(db)
    tool_stats = await service.get_tool_stats(limit)

    return Response(data=tool_stats)

"""
Tool log service.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any

from sqlalchemy import desc, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from api.models.tb_tool_log import TbToolLog
from api.schemas.tool_log_schema import (
    ToolStatsResponse,
    ToolTrendResponse,
    ToolUsageStatsResponse,
)
from api.utils.time_util import get_current_unix_ms

# Get logger
logger = logging.getLogger(__name__)


class ToolLogService:
    """
    Tool log service.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize tool log service.

        Args:
            db: Database session
        """
        self.db = db

    async def create_log(
        self,
        tool_name: str,
        call_type: str,
        tool_id: Optional[int] = None,
        request_time: Optional[int] = None,
        response_time: Optional[int] = None,
        duration_ms: Optional[int] = None,
        is_success: bool = False,
        error_message: Optional[str] = None,
        request_params: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> TbToolLog:
        """
        Create a new tool log.

        Args:
            tool_name: Tool name
            call_type: Call type (mcp, debug)
            tool_id: Tool ID
            request_time: Request time (UnixMS)
            response_time: Response time (UnixMS)
            duration_ms: Duration in milliseconds
            is_success: Whether the call was successful
            error_message: Error message if failed
            request_params: Request parameters
            response_data: Response data
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            TbToolLog: Created log
        """
        current_time = get_current_unix_ms()

        # Convert parameters and response data to JSON strings
        request_params_str = None
        if request_params:
            try:
                request_params_str = json.dumps(request_params, ensure_ascii=False)
            except Exception as e:
                logger.warning(f"Failed to serialize request_params: {str(e)}")

        response_data_str = None
        if response_data:
            try:
                response_data_str = json.dumps(response_data, ensure_ascii=False)
            except Exception as e:
                logger.warning(f"Failed to serialize response_data: {str(e)}")

        log = TbToolLog(
            tool_name=tool_name,
            tool_id=tool_id,
            call_type=call_type,
            request_time=request_time or current_time,
            response_time=response_time,
            duration_ms=duration_ms,
            is_success=is_success,
            error_message=error_message,
            request_params=request_params_str,
            response_data=response_data_str,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=current_time,
        )

        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)

        return log

    async def query_logs(
        self,
        page: int = 1,
        size: int = 20,
        tool_name: Optional[str] = None,
        call_type: Optional[str] = None,
        is_success: Optional[bool] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> Tuple[List[TbToolLog], int]:
        """
        Query tool logs with pagination.

        Args:
            page: Page number (1-based)
            size: Page size
            tool_name: Tool name filter
            call_type: Call type filter (mcp, debug)
            is_success: Success status filter
            start_time: Start time filter (UnixMS)
            end_time: End time filter (UnixMS)

        Returns:
            Tuple[List[TbToolLog], int]: List of logs and total count
        """
        query = select(TbToolLog)

        # Apply filters
        if tool_name:
            query = query.where(TbToolLog.tool_name.ilike(f"%{tool_name}%"))
        if call_type:
            query = query.where(TbToolLog.call_type == call_type)
        if is_success is not None:
            query = query.where(TbToolLog.is_success == is_success)
        if start_time:
            query = query.where(TbToolLog.request_time >= start_time)
        if end_time:
            query = query.where(TbToolLog.request_time <= end_time)

        # Count total
        count_query = select(func.count(TbToolLog.id))

        # Apply the same filters to count query
        if tool_name:
            count_query = count_query.where(TbToolLog.tool_name.ilike(f"%{tool_name}%"))
        if call_type:
            count_query = count_query.where(TbToolLog.call_type == call_type)
        if is_success is not None:
            count_query = count_query.where(TbToolLog.is_success == is_success)
        if start_time:
            count_query = count_query.where(TbToolLog.request_time >= start_time)
        if end_time:
            count_query = count_query.where(TbToolLog.request_time <= end_time)

        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # Apply pagination and ordering
        query = (
            query.order_by(desc(TbToolLog.request_time))
            .offset((page - 1) * size)
            .limit(size)
        )

        # Execute query
        result = await self.db.execute(query)
        logs = result.scalars().all()

        return list(logs), total

    async def get_stats(self) -> ToolStatsResponse:
        """
        Get tool statistics.

        Returns:
            ToolStatsResponse: Statistics
        """
        current_time = get_current_unix_ms()

        # Calculate time boundaries
        today_start = int(
            datetime.now()
            .replace(hour=0, minute=0, second=0, microsecond=0)
            .timestamp()
            * 1000
        )
        week_start = int((datetime.now() - timedelta(days=7)).timestamp() * 1000)
        month_start = int((datetime.now() - timedelta(days=30)).timestamp() * 1000)

        # Total calls
        total_result = await self.db.execute(select(func.count(TbToolLog.id)))
        total_calls = total_result.scalar() or 0

        # Success calls
        success_result = await self.db.execute(
            select(func.count(TbToolLog.id)).where(TbToolLog.is_success == True)
        )
        success_calls = success_result.scalar() or 0

        # Failed calls
        failed_calls = total_calls - success_calls

        # Success rate
        success_rate = (success_calls / total_calls * 100) if total_calls > 0 else 0

        # Average duration
        avg_duration_result = await self.db.execute(
            select(func.avg(TbToolLog.duration_ms)).where(
                TbToolLog.duration_ms.is_not(None)
            )
        )
        avg_duration_ms = avg_duration_result.scalar()

        # Calls today
        today_result = await self.db.execute(
            select(func.count(TbToolLog.id)).where(
                TbToolLog.request_time >= today_start
            )
        )
        calls_today = today_result.scalar() or 0

        # Calls this week
        week_result = await self.db.execute(
            select(func.count(TbToolLog.id)).where(TbToolLog.request_time >= week_start)
        )
        calls_this_week = week_result.scalar() or 0

        # Calls this month
        month_result = await self.db.execute(
            select(func.count(TbToolLog.id)).where(
                TbToolLog.request_time >= month_start
            )
        )
        calls_this_month = month_result.scalar() or 0

        # MCP calls
        mcp_result = await self.db.execute(
            select(func.count(TbToolLog.id)).where(TbToolLog.call_type == "mcp")
        )
        mcp_calls = mcp_result.scalar() or 0

        # Debug calls
        debug_result = await self.db.execute(
            select(func.count(TbToolLog.id)).where(TbToolLog.call_type == "debug")
        )
        debug_calls = debug_result.scalar() or 0

        return ToolStatsResponse(
            total_calls=total_calls,
            success_calls=success_calls,
            failed_calls=failed_calls,
            success_rate=round(success_rate, 2),
            avg_duration_ms=round(avg_duration_ms, 2) if avg_duration_ms else None,
            calls_today=calls_today,
            calls_this_week=calls_this_week,
            calls_this_month=calls_this_month,
            mcp_calls=mcp_calls,
            debug_calls=debug_calls,
        )

    async def get_trends(self, days: int = 7) -> List[ToolTrendResponse]:
        """
        Get tool trends for the last N days.

        Args:
            days: Number of days to get trends for

        Returns:
            List[ToolTrendResponse]: Trends
        """
        trends = []
        current_date = datetime.now().date()

        for i in range(days):
            date = current_date - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")

            # Calculate time boundaries for the day
            day_start = int(
                datetime.combine(date, datetime.min.time()).timestamp() * 1000
            )
            day_end = int(
                datetime.combine(date, datetime.max.time()).timestamp() * 1000
            )

            # Total calls for the day
            total_result = await self.db.execute(
                select(func.count(TbToolLog.id)).where(
                    and_(
                        TbToolLog.request_time >= day_start,
                        TbToolLog.request_time <= day_end,
                    )
                )
            )
            total_calls = total_result.scalar() or 0

            # Success calls for the day
            success_result = await self.db.execute(
                select(func.count(TbToolLog.id)).where(
                    and_(
                        TbToolLog.request_time >= day_start,
                        TbToolLog.request_time <= day_end,
                        TbToolLog.is_success == True,
                    )
                )
            )
            success_calls = success_result.scalar() or 0

            # Failed calls for the day
            failed_calls = total_calls - success_calls

            # MCP calls for the day
            mcp_result = await self.db.execute(
                select(func.count(TbToolLog.id)).where(
                    and_(
                        TbToolLog.request_time >= day_start,
                        TbToolLog.request_time <= day_end,
                        TbToolLog.call_type == "mcp",
                    )
                )
            )
            mcp_calls = mcp_result.scalar() or 0

            # Debug calls for the day
            debug_result = await self.db.execute(
                select(func.count(TbToolLog.id)).where(
                    and_(
                        TbToolLog.request_time >= day_start,
                        TbToolLog.request_time <= day_end,
                        TbToolLog.call_type == "debug",
                    )
                )
            )
            debug_calls = debug_result.scalar() or 0

            # Average duration for the day
            avg_duration_result = await self.db.execute(
                select(func.avg(TbToolLog.duration_ms)).where(
                    and_(
                        TbToolLog.request_time >= day_start,
                        TbToolLog.request_time <= day_end,
                        TbToolLog.duration_ms.is_not(None),
                    )
                )
            )
            avg_duration_ms = avg_duration_result.scalar()

            trends.append(
                ToolTrendResponse(
                    date=date_str,
                    total_calls=total_calls,
                    success_calls=success_calls,
                    failed_calls=failed_calls,
                    mcp_calls=mcp_calls,
                    debug_calls=debug_calls,
                    avg_duration_ms=round(avg_duration_ms, 2)
                    if avg_duration_ms
                    else None,
                )
            )

        return list(reversed(trends))  # Return in chronological order

    async def get_tool_stats(self, limit: int = 10) -> List[ToolUsageStatsResponse]:
        """
        Get tool statistics.

        Args:
            limit: Number of tools to return

        Returns:
            List[ToolUsageStatsResponse]: Tool statistics
        """
        # Get tool statistics
        result = await self.db.execute(
            select(
                TbToolLog.tool_name,
                TbToolLog.tool_id,
                func.count(TbToolLog.id).label("total_calls"),
                func.sum(case((TbToolLog.is_success == True, 1), else_=0)).label(
                    "success_calls"
                ),
                func.sum(case((TbToolLog.call_type == "mcp", 1), else_=0)).label(
                    "mcp_calls"
                ),
                func.sum(case((TbToolLog.call_type == "debug", 1), else_=0)).label(
                    "debug_calls"
                ),
                func.avg(TbToolLog.duration_ms).label("avg_duration_ms"),
                func.max(TbToolLog.request_time).label("last_call_time"),
            )
            .group_by(TbToolLog.tool_name, TbToolLog.tool_id)
            .order_by(desc("total_calls"))
            .limit(limit)
        )

        tool_stats = []
        for row in result:
            total_calls = row.total_calls or 0
            success_calls = row.success_calls or 0
            failed_calls = total_calls - success_calls
            mcp_calls = row.mcp_calls or 0
            debug_calls = row.debug_calls or 0
            success_rate = (success_calls / total_calls * 100) if total_calls > 0 else 0

            tool_stats.append(
                ToolUsageStatsResponse(
                    tool_name=row.tool_name,
                    tool_id=row.tool_id,
                    total_calls=total_calls,
                    success_calls=success_calls,
                    failed_calls=failed_calls,
                    mcp_calls=mcp_calls,
                    debug_calls=debug_calls,
                    success_rate=round(success_rate, 2),
                    avg_duration_ms=round(row.avg_duration_ms, 2)
                    if row.avg_duration_ms
                    else None,
                    last_call_time=row.last_call_time,
                )
            )

        return tool_stats

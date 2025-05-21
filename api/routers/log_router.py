"""
Log router.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import get_config
from api.database import get_db
from api.models.tb_user import TbUser
from api.schemas.log_schema import LogFilesResponse, LogContentResponse
from api.schemas.common_schema import Response
from api.services.log_service import LogService
from api.utils.security_util import get_current_user

# Get configuration
config = get_config()

# Create router
router = APIRouter(prefix="/log", tags=["log"])

# Create log service
log_service = LogService()


@router.get("", response_model=Response[LogFilesResponse])
async def get_log_files(
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Get list of available log files.

    Args:
        db: Database session
        current_user: Current user

    Returns:
        LogFilesResponse: List of log files
    """
    # 所有已登录用户都可以访问日志功能

    # Get log files
    files = log_service.get_log_files()

    return Response(data=LogFilesResponse(files=files))


@router.get("/content/{file_name}", response_model=Response[LogContentResponse])
async def get_log_content(
    file_name: str,
    max_lines: int = Query(1000, ge=1, le=10000, description="Maximum number of lines to return"),
    tail: bool = Query(True, description="If True, returns the last max_lines, otherwise returns from the beginning"),
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Get content of a log file.

    Args:
        file_name: Name of the log file
        max_lines: Maximum number of lines to return
        tail: If True, returns the last max_lines, otherwise returns from the beginning
        db: Database session
        current_user: Current user

    Returns:
        LogContentResponse: Log content
    """
    # 所有已登录用户都可以访问日志功能

    # Get log content
    content, total_lines = log_service.get_log_content(file_name, max_lines, tail)

    # Calculate displayed lines
    displayed_lines = content.count('\n') + (1 if content and not content.endswith('\n') else 0)

    return Response(
        data=LogContentResponse(
            file_name=file_name,
            content=content,
            total_lines=total_lines,
            displayed_lines=displayed_lines,
        )
    )

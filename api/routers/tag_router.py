"""
Tag router.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models.tb_user import TbUser
from api.schemas.common_schema import PaginatedResponse, Response
from api.schemas.tag_schema import (
    TagCreate,
    TagUpdate,
    TagResponse,
    TagWithToolCount,
)
from api.services.tag_service import TagService
from api.utils.security_util import get_current_user

# Create router
router = APIRouter(prefix="/tag", tags=["tag"])


@router.get("", response_model=PaginatedResponse[TagResponse])
async def get_tags(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=1000, description="Page size"),
    search: Optional[str] = Query(
        None, description="Search term for name or description"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Get tags with pagination.

    Args:
        page: Page number
        size: Page size
        search: Search term
        db: Database session
        current_user: Current user

    Returns:
        PaginatedResponse[TagResponse]: Paginated list of tags
    """
    service = TagService(db)
    tags, total = await service.query_tags(page, size, search)

    return PaginatedResponse(
        data=[TagResponse.model_validate(tag.__dict__) for tag in tags], total=total
    )


@router.get("/with-count", response_model=PaginatedResponse[TagWithToolCount])
async def get_tags_with_tool_count(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=1000, description="Page size"),
    search: Optional[str] = Query(
        None, description="Search term for name or description"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Get tags with tool count.

    Args:
        page: Page number
        size: Page size
        search: Search term
        db: Database session
        current_user: Current user

    Returns:
        PaginatedResponse[TagWithToolCount]: Paginated list of tags with tool count
    """
    service = TagService(db)
    tags_with_count, total = await service.get_tags_with_tool_count(page, size, search)

    return PaginatedResponse(
        data=[TagWithToolCount.model_validate(tag) for tag in tags_with_count],
        total=total,
    )


@router.post("", response_model=Response[TagResponse])
async def create_tag(
    tag_data: TagCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Create a new tag.

    Args:
        tag_data: Tag data
        db: Database session
        current_user: Current user

    Returns:
        Response[TagResponse]: Created tag
    """
    service = TagService(db)
    tag = await service.create_tag(tag_data, current_user.username)

    return Response(data=TagResponse.model_validate(tag.__dict__))


@router.get("/{tag_id}", response_model=Response[TagResponse])
async def get_tag(
    tag_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Get tag by ID.

    Args:
        tag_id: Tag ID
        db: Database session
        current_user: Current user

    Returns:
        Response[TagResponse]: Tag details
    """
    service = TagService(db)
    tag = await service.get_tag_by_id(tag_id)

    if not tag:
        from api.errors.tag_error import TagNotFoundError

        raise TagNotFoundError(tag_id=tag_id)

    return Response(data=TagResponse.model_validate(tag.__dict__))


@router.put("/{tag_id}", response_model=Response[TagResponse])
async def update_tag(
    tag_id: int,
    tag_data: TagUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Update a tag.

    Args:
        tag_id: Tag ID
        tag_data: Tag update data
        db: Database session
        current_user: Current user

    Returns:
        Response[TagResponse]: Updated tag
    """
    service = TagService(db)
    tag = await service.update_tag(tag_id, tag_data, current_user.username)

    return Response(data=TagResponse.model_validate(tag.__dict__))


@router.delete("/{tag_id}", response_model=Response[None])
async def delete_tag(
    tag_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Delete a tag.

    Args:
        tag_id: Tag ID
        db: Database session
        current_user: Current user

    Returns:
        Response[None]: Success response
    """
    service = TagService(db)
    await service.delete_tag(tag_id, current_user.username)

    return Response(data=None, message="Tag deleted successfully")

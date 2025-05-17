"""
User router.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models.tb_user import TbUser
from api.schemas.common_schema import Response, PaginatedResponse
from api.schemas.user_schema import UserCreate, UserUpdate, UserResponse
from api.services.user_service import UserService
from api.utils.security_util import get_current_user

# Create router
router = APIRouter(prefix="/user", tags=["user"])


@router.get("", response_model=PaginatedResponse[UserResponse])
async def get_users(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(
        None, description="Search term for username or email"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Get users with pagination.

    Args:
        page: Page number
        size: Page size
        search: Search term for username or email
        db: Database session
        current_user: Current user

    Returns:
        PaginatedResponse[UserResponse]: Paginated list of users
    """
    service = UserService(db)
    users, total = await service.query_users(page, size, search)

    return PaginatedResponse(
        data=[UserResponse.model_validate(user) for user in users], total=total
    )


@router.post("", response_model=Response[UserResponse])
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Create a new user.

    Args:
        user_data: User data
        db: Database session
        current_user: Current user

    Returns:
        Response[UserResponse]: Created user
    """
    service = UserService(db)
    user = await service.create_user(user_data, current_user.username)

    return Response(data=UserResponse.model_validate(user))


@router.get("/{user_id}", response_model=Response[UserResponse])
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Get user by ID.

    Args:
        user_id: User ID
        db: Database session
        current_user: Current user

    Returns:
        Response[UserResponse]: User
    """
    service = UserService(db)
    user = await service.get_user_by_id(user_id)

    return Response(data=UserResponse.model_validate(user) if user else None)


@router.put("/{user_id}", response_model=Response[UserResponse])
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Update user.

    Args:
        user_id: User ID
        user_data: User data
        db: Database session
        current_user: Current user

    Returns:
        Response[UserResponse]: Updated user
    """
    service = UserService(db)
    user = await service.update_user(user_id, user_data, current_user.username)

    return Response(data=UserResponse.model_validate(user) if user else None)


@router.delete("/{user_id}", response_model=Response[UserResponse])
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Delete user.

    Args:
        user_id: User ID
        db: Database session
        current_user: Current user

    Returns:
        Response[UserResponse]: Deleted user
    """
    service = UserService(db)
    user = await service.delete_user(user_id, current_user.username)

    return Response(data=UserResponse.model_validate(user) if user else None)

"""
Function router.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models.tb_user import TbUser
from api.schemas.func_schema import (
    FuncCreate,
    FuncUpdate,
    FuncResponse,
    FuncDeployResponse,
)
from api.schemas.common_schema import Response, PaginatedResponse
from api.schemas.usage_schema import FuncUsageResponse
from api.services.func_service import FuncService
from api.utils.security_util import get_current_user

# Create router
router = APIRouter(prefix="/func", tags=["func"])


@router.get("", response_model=PaginatedResponse[FuncResponse])
async def get_funcs(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(
        None, description="Search term for name or description"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Get functions with pagination.

    Args:
        page: Page number
        size: Page size
        search: Search term
        db: Database session
        current_user: Current user

    Returns:
        PaginatedResponse[FuncResponse]: Paginated list of functions
    """
    service = FuncService(db)
    funcs, total = await service.query_funcs(page, size, search)

    return PaginatedResponse(
        data=[FuncResponse.model_validate(func) for func in funcs], total=total
    )


@router.post("", response_model=Response[FuncResponse])
async def create_func(
    func_data: FuncCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Create a new function.

    Args:
        func_data: Function data
        db: Database session
        current_user: Current user

    Returns:
        Response[FuncResponse]: Created function
    """
    service = FuncService(db)
    func = await service.create_func(func_data, current_user.username)

    return Response(data=FuncResponse.model_validate(func))


@router.post("/deploy", response_model=Response[FuncResponse])
async def create_and_deploy_func(
    func_data: FuncCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Create a new function and deploy it.

    Args:
        func_data: Function data
        db: Database session
        current_user: Current user

    Returns:
        Response[FuncResponse]: Created and deployed function
    """
    service = FuncService(db)
    func = await service.create_func(func_data, current_user.username)
    await service.deploy_func(func.id, "Initial deployment", current_user.username)

    # Refresh function to get updated version
    func = await service.get_func_by_id(func.id)

    return Response(data=FuncResponse.model_validate(func))


@router.get("/{func_id}", response_model=Response[FuncResponse])
async def get_func(
    func_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Get function by ID.

    Args:
        func_id: Function ID
        db: Database session
        current_user: Current user

    Returns:
        Response[FuncResponse]: Function
    """
    service = FuncService(db)
    func = await service.get_func_by_id(func_id)

    return Response(data=FuncResponse.model_validate(func) if func else None)


@router.put("/{func_id}", response_model=Response[FuncResponse])
async def update_func(
    func_id: int,
    func_data: FuncUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Update function.

    Args:
        func_id: Function ID
        func_data: Function data
        db: Database session
        current_user: Current user

    Returns:
        Response[FuncResponse]: Updated function
    """
    service = FuncService(db)
    func = await service.update_func(func_id, func_data, current_user.username)

    return Response(data=FuncResponse.model_validate(func) if func else None)


@router.put("/{func_id}/deploy", response_model=Response[FuncResponse])
async def update_and_deploy_func(
    func_id: int,
    func_data: FuncUpdate,
    description: Optional[str] = Query(None, description="Deployment description"),
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Update function and deploy it.

    Args:
        func_id: Function ID
        func_data: Function data
        description: Deployment description
        db: Database session
        current_user: Current user

    Returns:
        Response[FuncResponse]: Updated and deployed function
    """
    service = FuncService(db)
    func = await service.update_func(func_id, func_data, current_user.username)
    await service.deploy_func(func_id, description, current_user.username)

    # Refresh function to get updated version
    func = await service.get_func_by_id(func_id)

    return Response(data=FuncResponse.model_validate(func) if func else None)


@router.get(
    "/{func_id}/deploy/history", response_model=PaginatedResponse[FuncDeployResponse]
)
async def get_func_deploy_history(
    func_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Get function deployment history.

    Args:
        func_id: Function ID
        page: Page number
        size: Page size
        db: Database session
        current_user: Current user

    Returns:
        PaginatedResponse[FuncDeployResponse]: Paginated list of function deployments
    """
    service = FuncService(db)
    deploys, total = await service.get_func_deploy_history(func_id, page, size)

    return PaginatedResponse(
        data=[FuncDeployResponse.model_validate(deploy) for deploy in deploys],
        total=total,
    )


@router.post(
    "/{func_id}/deploy/rollback/{version}", response_model=Response[FuncResponse]
)
async def rollback_func(
    func_id: int,
    version: int,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Rollback function to a specific version.

    Args:
        func_id: Function ID
        version: Version to rollback to
        db: Database session
        current_user: Current user

    Returns:
        Response[FuncResponse]: Rolled back function
    """
    service = FuncService(db)
    func = await service.rollback_func(func_id, version, current_user.username)

    return Response(data=FuncResponse.model_validate(func))


@router.delete("/{func_id}", response_model=Response[FuncResponse])
async def delete_func(
    func_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Delete function.

    Args:
        func_id: Function ID
        db: Database session
        current_user: Current user

    Returns:
        Response[FuncResponse]: Deleted function
    """
    service = FuncService(db)
    func = await service.delete_func(func_id, current_user.username)

    return Response(data=FuncResponse.model_validate(func) if func else None)


@router.get("/{func_id}/usage", response_model=Response[FuncUsageResponse])
async def get_func_usage(
    func_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Get usage information for a function.

    Args:
        func_id: Function ID
        db: Database session
        current_user: Current user

    Returns:
        Response[FuncUsageResponse]: Usage information for the function
    """
    service = FuncService(db)
    usage = await service.get_func_usage(func_id)

    return Response(data=usage)


@router.get("/{func_id}/depend", response_model=Response[List[FuncResponse]])
async def get_func_dependencies(
    func_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Get dependencies of a function.

    Args:
        func_id: Function ID
        db: Database session
        current_user: Current user

    Returns:
        Response[List[FuncResponse]]: List of functions this function depends on
    """
    service = FuncService(db)
    dependencies = await service.get_func_dependencies(func_id)

    return Response(data=dependencies)

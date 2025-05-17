"""
Configuration router.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models.tb_user import TbUser
from api.schemas.common_schema import Response, PaginatedResponse
from api.schemas.config_schema import ConfigCreate, ConfigUpdate, ConfigResponse
from api.schemas.usage_schema import ConfigUsageResponse
from api.services.config_service import ConfigService
from api.utils.security_util import get_current_user

# Create router
router = APIRouter(prefix="/config", tags=["config"])


@router.get("", response_model=PaginatedResponse[ConfigResponse])
async def get_configs(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(
        None, description="Search term for name or description"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Get configurations with pagination.

    Args:
        page: Page number
        size: Page size
        search: Search term
        db: Database session
        current_user: Current user

    Returns:
        PaginatedResponse[ConfigResponse]: Paginated list of configurations
    """
    service = ConfigService(db)
    configs, total = await service.query_configs(page, size, search)

    return PaginatedResponse(
        data=[ConfigResponse.model_validate(config) for config in configs], total=total
    )


@router.post("", response_model=Response[ConfigResponse])
async def create_config(
    config_data: ConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Create a new configuration.

    Args:
        config_data: Configuration data
        db: Database session
        current_user: Current user

    Returns:
        Response[ConfigResponse]: Created configuration
    """
    service = ConfigService(db)
    config = await service.create_config(config_data, current_user.username)

    return Response(data=ConfigResponse.model_validate(config))


@router.get("/{config_id}", response_model=Response[ConfigResponse])
async def get_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Get configuration by ID.

    Args:
        config_id: Configuration ID
        db: Database session
        current_user: Current user

    Returns:
        Response[ConfigResponse]: Configuration
    """
    service = ConfigService(db)
    config = await service.get_config_by_id(config_id)

    return Response(data=ConfigResponse.model_validate(config) if config else None)


@router.put("/{config_id}", response_model=Response[ConfigResponse])
async def update_config(
    config_id: int,
    config_data: ConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Update configuration.

    Args:
        config_id: Configuration ID
        config_data: Configuration data
        db: Database session
        current_user: Current user

    Returns:
        Response[ConfigResponse]: Updated configuration
    """
    service = ConfigService(db)
    config = await service.update_config(config_id, config_data, current_user.username)

    return Response(data=ConfigResponse.model_validate(config) if config else None)


@router.delete("/{config_id}", response_model=Response[ConfigResponse])
async def delete_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Delete configuration.

    Args:
        config_id: Configuration ID
        db: Database session
        current_user: Current user

    Returns:
        Response[ConfigResponse]: Deleted configuration
    """
    service = ConfigService(db)
    config = await service.delete_config(config_id, current_user.username)

    return Response(data=ConfigResponse.model_validate(config) if config else None)


@router.get("/{config_id}/usage", response_model=Response[ConfigUsageResponse])
async def get_config_usage(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Get usage information for a configuration.

    Args:
        config_id: Configuration ID
        db: Database session
        current_user: Current user

    Returns:
        Response[ConfigUsageResponse]: Usage information for the configuration
    """
    service = ConfigService(db)
    usage = await service.get_config_usage(config_id)

    return Response(data=usage)

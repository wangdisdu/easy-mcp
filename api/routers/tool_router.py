"""
Tool router.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.errors.tool_error import ToolExecutionError
from api.models.tb_user import TbUser
from api.schemas.common_schema import PaginatedResponse, Response
from api.schemas.config_schema import ConfigResponse
from api.schemas.func_schema import FuncResponse
from api.schemas.tool_schema import (
    ToolCreate,
    ToolDebugRequest,
    ToolDebugResponse,
    ToolDeployResponse,
    ToolResponse,
    ToolUpdate,
)
from api.services.tool_service import ToolService
from api.utils.security_util import get_current_user

# Create router
router = APIRouter(prefix="/tool", tags=["tool"])


@router.get("", response_model=PaginatedResponse[ToolResponse])
async def get_tools(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(
        None, description="Search term for name or description"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Get tools with pagination.

    Args:
        page: Page number
        size: Page size
        search: Search term
        db: Database session
        current_user: Current user

    Returns:
        PaginatedResponse[ToolResponse]: Paginated list of tools
    """
    service = ToolService(db)
    tools, total = await service.query_tools(page, size, search)

    return PaginatedResponse(
        data=[ToolResponse.model_validate(tool) for tool in tools], total=total
    )


@router.post("", response_model=Response[ToolResponse])
async def create_tool(
    tool_data: ToolCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Create a new tool.

    Args:
        tool_data: Tool data
        db: Database session
        current_user: Current user

    Returns:
        Response[ToolResponse]: Created tool
    """
    service = ToolService(db)
    tool = await service.create_tool(tool_data, current_user.username)

    return Response(data=ToolResponse.model_validate(tool))


@router.post("/deploy", response_model=Response[ToolResponse])
async def create_and_deploy_tool(
    tool_data: ToolCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Create a new tool and deploy it.

    Args:
        tool_data: Tool data
        db: Database session
        current_user: Current user

    Returns:
        Response[ToolResponse]: Created and deployed tool
    """
    service = ToolService(db)
    tool = await service.create_tool(tool_data, current_user.username)
    await service.deploy_tool(tool.id, "Initial deployment", current_user.username)

    # Refresh tool to get updated version
    tool = await service.get_tool_by_id(tool.id)

    return Response(data=ToolResponse.model_validate(tool))


@router.get("/{tool_id}", response_model=Response[ToolResponse])
async def get_tool(
    tool_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Get tool by ID.

    Args:
        tool_id: Tool ID
        db: Database session
        current_user: Current user

    Returns:
        Response[ToolResponse]: Tool
    """
    service = ToolService(db)
    tool = await service.get_tool_by_id(tool_id)

    return Response(data=ToolResponse.model_validate(tool) if tool else None)


@router.put("/{tool_id}", response_model=Response[ToolResponse])
async def update_tool(
    tool_id: int,
    tool_data: ToolUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Update tool.

    Args:
        tool_id: Tool ID
        tool_data: Tool data
        db: Database session
        current_user: Current user

    Returns:
        Response[ToolResponse]: Updated tool
    """
    service = ToolService(db)
    tool = await service.update_tool(tool_id, tool_data, current_user.username)

    return Response(data=ToolResponse.model_validate(tool) if tool else None)


@router.put("/{tool_id}/deploy", response_model=Response[ToolResponse])
async def update_and_deploy_tool(
    tool_id: int,
    tool_data: ToolUpdate,
    description: Optional[str] = Query(None, description="Deployment description"),
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Update tool and deploy it.

    Args:
        tool_id: Tool ID
        tool_data: Tool data
        description: Deployment description
        db: Database session
        current_user: Current user

    Returns:
        Response[ToolResponse]: Updated and deployed tool
    """
    service = ToolService(db)
    tool = await service.update_tool(tool_id, tool_data, current_user.username)
    await service.deploy_tool(tool_id, description, current_user.username)

    # Refresh tool to get updated version
    tool = await service.get_tool_by_id(tool_id)

    return Response(data=ToolResponse.model_validate(tool) if tool else None)


@router.get(
    "/{tool_id}/deploy/history", response_model=PaginatedResponse[ToolDeployResponse]
)
async def get_tool_deploy_history(
    tool_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Get tool deployment history.

    Args:
        tool_id: Tool ID
        page: Page number
        size: Page size
        db: Database session
        current_user: Current user

    Returns:
        PaginatedResponse[ToolDeployResponse]: Paginated list of tool deployments
    """
    service = ToolService(db)
    deploys, total = await service.get_tool_deploy_history(tool_id, page, size)

    return PaginatedResponse(
        data=[ToolDeployResponse.model_validate(deploy) for deploy in deploys],
        total=total,
    )


@router.post(
    "/{tool_id}/deploy/rollback/{version}", response_model=Response[ToolResponse]
)
async def rollback_tool(
    tool_id: int,
    version: int,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Rollback tool to a specific version.

    Args:
        tool_id: Tool ID
        version: Version to rollback to
        db: Database session
        current_user: Current user

    Returns:
        Response[ToolResponse]: Rolled back tool
    """
    service = ToolService(db)
    tool = await service.rollback_tool(tool_id, version, current_user.username)

    return Response(data=ToolResponse.model_validate(tool))


@router.delete("/{tool_id}", response_model=Response[ToolResponse])
async def delete_tool(
    tool_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Delete tool.

    Args:
        tool_id: Tool ID
        db: Database session
        current_user: Current user

    Returns:
        Response[ToolResponse]: Deleted tool
    """
    service = ToolService(db)
    tool = await service.delete_tool(tool_id, current_user.username)

    return Response(data=ToolResponse.model_validate(tool) if tool else None)


@router.post("/{tool_id}/debug", response_model=Response[ToolDebugResponse])
async def debug_tool(
    tool_id: int,
    debug_data: ToolDebugRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Debug tool execution.

    Args:
        tool_id: Tool ID
        debug_data: Debug data
        db: Database session
        current_user: Current user

    Returns:
        Response[ToolDebugResponse]: Debug result
    """
    service = ToolService(db)

    try:
        result, logs = await service.execute_tool(tool_id, debug_data.parameters)
        return Response(
            data=ToolDebugResponse(
                result=result, logs=logs, success=True, error_message=None
            )
        )
    except ToolExecutionError as e:
        # Return a successful response with error details
        return Response(
            data=ToolDebugResponse(
                result=None,
                logs=logs if "logs" in locals() else [],
                success=False,
                error_message=e.description,
            )
        )


@router.get("/{tool_id}/func", response_model=Response[List[FuncResponse]])
async def get_tool_functions(
    tool_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Get functions associated with a tool.

    Args:
        tool_id: Tool ID
        db: Database session
        current_user: Current user

    Returns:
        Response[List[FuncResponse]]: List of functions associated with the tool
    """
    service = ToolService(db)
    funcs = await service.get_tool_funcs(tool_id)

    func_responses = [FuncResponse.model_validate(func) for func in funcs]

    return Response(data=func_responses)


@router.get("/{tool_id}/config", response_model=Response[List[ConfigResponse]])
async def get_tool_configs(
    tool_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Get configurations associated with a tool.

    Args:
        tool_id: Tool ID
        db: Database session
        current_user: Current user

    Returns:
        Response[List[ConfigResponse]]: List of configurations associated with the tool
    """
    service = ToolService(db)
    configs = await service.get_tool_configs(tool_id)

    config_responses = [ConfigResponse.model_validate(config) for config in configs]

    return Response(data=config_responses)


@router.patch("/{tool_id}/enable", response_model=Response[ToolResponse])
async def enable_tool(
    tool_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Enable tool.

    Args:
        tool_id: Tool ID
        db: Database session
        current_user: Current user

    Returns:
        Response[ToolResponse]: Response with updated tool
    """
    tool_service = ToolService(db)
    tool = await tool_service.toggle_tool_state(tool_id, True, current_user.username)
    return Response(data=ToolResponse.model_validate(tool))


@router.patch("/{tool_id}/disable", response_model=Response[ToolResponse])
async def disable_tool(
    tool_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Disable tool.

    Args:
        tool_id: Tool ID
        db: Database session
        current_user: Current user

    Returns:
        Response[ToolResponse]: Response with updated tool
    """
    tool_service = ToolService(db)
    tool = await tool_service.toggle_tool_state(tool_id, False, current_user.username)
    return Response(data=ToolResponse.model_validate(tool))

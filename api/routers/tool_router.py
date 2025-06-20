"""
Tool router.
"""

from typing import List, Optional, Any
import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.errors.tool_error import ToolExecutionError, ToolNotFoundError
from api.models.tb_user import TbUser
from api.schemas.common_schema import PaginatedResponse, Response
from api.schemas.config_schema import ConfigResponse
from api.schemas.func_schema import FuncResponse
from api.schemas.tool_schema import (
    BuiltinToolImportRequest,
    BuiltinToolListResponse,
    ToolCreate,
    ToolDebugRequest,
    ToolDebugResponse,
    ToolDeployResponse,
    ToolResponse,
    ToolUpdate,
    ToolMcpResponse,
    ToolMcpExecuteRequest,
)
from api.schemas.tag_schema import TagResponse, ToolTagRequest
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
    tag_ids: Optional[str] = Query(
        None, description="Comma-separated tag IDs to filter by"
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
        tag_ids: Comma-separated tag IDs to filter by (e.g., "1,2,3")
        db: Database session
        current_user: Current user

    Returns:
        PaginatedResponse[ToolResponse]: Paginated list of tools
    """
    service = ToolService(db)

    # Parse comma-separated tag_ids string to list of integers
    parsed_tag_ids = None
    if tag_ids:
        try:
            parsed_tag_ids = [
                int(tag_id.strip()) for tag_id in tag_ids.split(",") if tag_id.strip()
            ]
        except ValueError:
            parsed_tag_ids = None

    tools, total = await service.query_tools(page, size, search, parsed_tag_ids)

    # Load tags for each tool
    tool_responses = []
    for tool in tools:
        tags = await service.get_tool_tags(tool.id)
        tool_dict = tool.__dict__.copy()
        tool_dict["tags"] = [tag.__dict__ for tag in tags]
        tool_responses.append(ToolResponse.model_validate(tool_dict))

    return PaginatedResponse(data=tool_responses, total=total)


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

    if tool:
        tags = await service.get_tool_tags(tool.id)
        tool_dict = tool.__dict__.copy()
        tool_dict["tags"] = [tag.__dict__ for tag in tags]
        return Response(data=ToolResponse.model_validate(tool_dict))
    else:
        return Response(data=None)


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
        result, logs = await service.execute_tool(
            tool_id, debug_data.parameters, call_type="debug"
        )
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


@router.get("-builtin", response_model=Response[BuiltinToolListResponse])
async def list_builtin_tools(
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    List all builtin tools.

    Returns:
        Response[BuiltinToolListResponse]: List of builtin tools
    """
    service = ToolService(db)
    response = await service.list_builtin_tools()
    return Response(data=response)


@router.post("-builtin/import", response_model=Response[ToolResponse])
async def import_builtin_tool(
    import_data: BuiltinToolImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Import a builtin tool.

    Args:
        import_data: Import data
        db: Database session
        current_user: Current user

    Returns:
        Response[ToolResponse]: Imported tool
    """
    service = ToolService(db)
    tool = await service.import_builtin_tool(import_data.tool_id, current_user.username)
    return Response(data=ToolResponse.model_validate(tool))


@router.get("-mcp", response_model=Response[List[ToolMcpResponse]])
async def list_mcp_tools(
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    List all tools available for MCP.

    Returns:
        Response[List[ToolMcpResponse]]: List of tools with name, description and parameters
    """
    service = ToolService(db)
    tools, _ = await service.query_tools(page=1, size=1000)  # Get all tools

    # Filter enabled tools and map to MCP response
    mcp_tools = [
        ToolMcpResponse(
            name=tool.name,
            description=tool.description,
            parameters=json.loads(tool.parameters),
        )
        for tool in tools
        if tool.is_enabled
    ]

    return Response(data=mcp_tools)


@router.post("-mcp/{name}/execute", response_model=Response[Any])
async def execute_mcp_tool(
    name: str,
    execute_data: ToolMcpExecuteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Execute a tool by name.

    Args:
        name: Tool name
        execute_data: Execution parameters
        db: Database session
        current_user: Current user

    Returns:
        Response[Any]: Execution result
    """
    service = ToolService(db)

    # Get tool by name
    tool = await service.get_tool_by_name(name)
    if not tool:
        raise ToolNotFoundError(name=name)

    try:
        result, logs = await service.execute_tool(
            tool.id, execute_data.parameters, call_type="mcp"
        )
        return Response(data=result)
    except ToolExecutionError as e:
        return Response(data=e.description)


@router.get("/{tool_id}/tags", response_model=Response[List[TagResponse]])
async def get_tool_tags(
    tool_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Get tags associated with a tool.

    Args:
        tool_id: Tool ID
        db: Database session
        current_user: Current user

    Returns:
        Response[List[TagResponse]]: List of tags associated with the tool
    """
    service = ToolService(db)
    tags = await service.get_tool_tags(tool_id)

    return Response(data=[TagResponse.model_validate(tag.__dict__) for tag in tags])


@router.put("/{tool_id}/tags", response_model=Response[None])
async def set_tool_tags(
    tool_id: int,
    tag_request: ToolTagRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Set tags for a tool (replace all existing tags).

    This is the only way to manage tool tags - it completely replaces
    all existing tags with the provided list.

    Args:
        tool_id: Tool ID
        tag_request: Tag request data containing list of tag IDs
        db: Database session
        current_user: Current user

    Returns:
        Response[None]: Success response
    """
    service = ToolService(db)
    await service.set_tool_tags(tool_id, tag_request.tag_ids, current_user.username)

    return Response(data=None, message="Tags set successfully")

"""
Tool service.
"""

import io
import json
import logging
import os
import traceback
from contextlib import redirect_stdout, redirect_stderr
from typing import Optional, List, Tuple, Dict, Any

import yaml
from sqlalchemy import or_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from api.errors.tool_error import (
    ToolNotFoundError,
    ToolAlreadyExistsError,
    ToolVersionNotFoundError,
    ToolExecutionError,
    ToolStateChangeError,
)
from api.models.tb_config import TbConfig
from api.models.tb_func import TbFunc
from api.models.tb_tool import TbTool, TbToolDeploy, TbToolFunc, TbToolConfig
from api.schemas.config_schema import ConfigCreate
from api.schemas.tool_schema import (
    ToolCreate,
    ToolUpdate,
    BuiltinToolInfo,
    BuiltinToolListResponse,
)
from api.utils.audit_util import audit
from api.utils.time_util import get_current_unix_ms

# Get logger
logger = logging.getLogger(__name__)


class ToolService:
    """
    Tool service.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize tool service.

        Args:
            db: Database session
        """
        self.db = db

    async def get_tool_by_id(self, tool_id: int) -> Optional[TbTool]:
        """
        Get tool by ID.

        Args:
            tool_id: Tool ID

        Returns:
            TbTool: Tool object or None if not found
        """
        result = await self.db.execute(select(TbTool).where(TbTool.id == tool_id))
        return result.scalars().first()

    async def get_tool_by_name(self, name: str) -> Optional[TbTool]:
        """
        Get tool by name.

        Args:
            name: Tool name

        Returns:
            TbTool: Tool object or None if not found
        """
        result = await self.db.execute(select(TbTool).where(TbTool.name == name))
        return result.scalars().first()

    async def query_tools(
        self, page: int = 1, size: int = 20, search: Optional[str] = None
    ) -> Tuple[List[TbTool], int]:
        """
        Query tools with pagination.

        Args:
            page: Page number (1-based)
            size: Page size
            search: Search term for name or description

        Returns:
            Tuple[List[TbTool], int]: List of tools and total count
        """
        query = select(TbTool)

        # Apply filters
        if search:
            query = query.where(
                or_(
                    TbTool.name.ilike(f"%{search}%"),
                    TbTool.description.ilike(f"%{search}%"),
                )
            )

        # Count total
        count_query = select(func.count(TbTool.id))

        # Apply the same filters to count query
        if search:
            count_query = count_query.where(
                or_(
                    TbTool.name.ilike(f"%{search}%"),
                    TbTool.description.ilike(f"%{search}%"),
                )
            )

        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # Apply pagination and ordering
        query = query.order_by(desc(TbTool.id)).offset((page - 1) * size).limit(size)

        # Execute query
        result = await self.db.execute(query)
        tools = result.scalars().all()

        return list(tools), total

    @audit(operation_type="create", object_type="tool")
    async def create_tool(
        self, tool_data: ToolCreate, current_user: Optional[str] = None
    ) -> TbTool:
        """
        Create a new tool.

        Args:
            tool_data: Tool data
            current_user: Current username

        Returns:
            TbTool: Created tool

        Raises:
            ToolAlreadyExistsError: If tool already exists
        """
        # Check if tool already exists
        existing_tool = await self.get_tool_by_name(tool_data.name)
        if existing_tool:
            logger.warning(
                f"Refuse to create tool with existing name: {tool_data.name}"
            )
            raise ToolAlreadyExistsError(name=tool_data.name)

        # For HTTP tools, ensure easy_http_call function exists
        if tool_data.type == 'http':
            # Check if easy_http_call function exists
            result = await self.db.execute(
                select(TbFunc).where(TbFunc.name == 'easy_http_call')
            )
            http_func = result.scalars().first()

            if not http_func:
                # Create easy_http_call function
                current_time = get_current_unix_ms()
                http_func = TbFunc(
                    name='easy_http_call',
                    description='HTTP request helper function',
                    code='''def easy_http_call(url, headers, parameters, config):
    """
    Make HTTP request with parameters.
    
    Args:
        url: Request URL
        headers: Request headers
        parameters: Request parameters
        config: Tool configuration
    
    Returns:
        dict: Response data
    """
    import requests
    import json
    
    # Process URL parameters
    if parameters:
        for key, value in parameters.items():
            if isinstance(value, dict) and value.get('location') == 'url':
                # Replace URL parameters
                url = url.replace(f"{{{key}}}", str(value.get('value', '')))
    
    # Process header parameters
    if parameters:
        for key, value in parameters.items():
            if isinstance(value, dict) and value.get('location') == 'header':
                # Add to headers
                headers[key] = str(value.get('value', ''))
    
    # Make request
    response = requests.request(
        method='POST',
        url=url,
        headers=headers,
        json=parameters,
        timeout=30
    )
    
    # Return response
    return {
        'status_code': response.status_code,
        'headers': dict(response.headers),
        'data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
    }''',
                    created_at=current_time,
                    updated_at=current_time,
                    created_by=current_user,
                    updated_by=current_user
                )
                self.db.add(http_func)
                await self.db.commit()
                await self.db.refresh(http_func)

            # Add easy_http_call to func_ids if not already included
            if tool_data.func_ids is None:
                tool_data.func_ids = []
            if http_func.id not in tool_data.func_ids:
                tool_data.func_ids.append(http_func.id)

        # Create tool
        current_time = get_current_unix_ms()
        tool = TbTool(
            name=tool_data.name,
            description=tool_data.description,
            parameters=json.dumps(tool_data.parameters),
            code=tool_data.code,
            type=tool_data.type,
            setting=json.dumps(tool_data.setting),
            is_enabled=True,
            created_at=current_time,
            updated_at=current_time,
            created_by=current_user,
            updated_by=current_user,
        )

        self.db.add(tool)
        await self.db.commit()
        await self.db.refresh(tool)

        # Add function associations
        if tool_data.func_ids:
            for func_id in tool_data.func_ids:
                tool_func = TbToolFunc(
                    tool_id=tool.id,
                    func_id=func_id,
                    created_at=current_time,
                    updated_at=current_time,
                    created_by=current_user,
                    updated_by=current_user,
                )
                self.db.add(tool_func)

        # Add config associations
        if tool_data.config_ids:
            for config_id in tool_data.config_ids:
                tool_config = TbToolConfig(
                    tool_id=tool.id,
                    config_id=config_id,
                    created_at=current_time,
                    updated_at=current_time,
                    created_by=current_user,
                    updated_by=current_user,
                )
                self.db.add(tool_config)

        await self.db.commit()

        return tool

    @audit(operation_type="update", object_type="tool")
    async def update_tool(
        self, tool_id: int, tool_data: ToolUpdate, current_user: Optional[str] = None
    ) -> Optional[TbTool]:
        """
        Update tool.

        Args:
            tool_id: Tool ID
            tool_data: Tool data
            current_user: Current username

        Returns:
            TbTool: Updated tool or None if not found

        Raises:
            ToolNotFoundError: If tool not found
            ToolAlreadyExistsError: If tool name already exists
        """
        # Get tool
        tool = await self.get_tool_by_id(tool_id)
        if not tool:
            logger.error(f"Tool not found for update operation: {tool_id}")
            raise ToolNotFoundError(tool_id=tool_id)

        # Check if name already exists
        if tool_data.name != tool.name:
            existing_tool = await self.get_tool_by_name(tool_data.name)
            if existing_tool:
                logger.warning(
                    f"Refuse to update tool with existing name: {tool_data.name}"
                )
                raise ToolAlreadyExistsError(name=tool_data.name)

        # Update tool
        tool.name = tool_data.name
        tool.description = tool_data.description
        tool.parameters = json.dumps(tool_data.parameters)
        tool.code = tool_data.code
        tool.type = tool_data.type
        tool.setting = json.dumps(tool_data.setting)
        tool.updated_at = get_current_unix_ms()
        tool.updated_by = current_user

        # Update function associations
        if tool_data.func_ids is not None:
            # Delete existing associations
            await self.db.execute(
                TbToolFunc.__table__.delete().where(TbToolFunc.tool_id == tool_id)
            )

            # Add new associations
            current_time = get_current_unix_ms()
            for func_id in tool_data.func_ids:
                tool_func = TbToolFunc(
                    tool_id=tool.id,
                    func_id=func_id,
                    created_at=current_time,
                    updated_at=current_time,
                    created_by=current_user,
                    updated_by=current_user,
                )
                self.db.add(tool_func)

        # Update config associations
        if tool_data.config_ids is not None:
            # Delete existing associations
            await self.db.execute(
                TbToolConfig.__table__.delete().where(TbToolConfig.tool_id == tool_id)
            )

            # Add new associations
            current_time = get_current_unix_ms()
            for config_id in tool_data.config_ids:
                tool_config = TbToolConfig(
                    tool_id=tool.id,
                    config_id=config_id,
                    created_at=current_time,
                    updated_at=current_time,
                    created_by=current_user,
                    updated_by=current_user,
                )
                self.db.add(tool_config)

        await self.db.commit()
        await self.db.refresh(tool)

        return tool

    @audit(operation_type="deploy", object_type="tool")
    async def deploy_tool(
        self,
        tool_id: int,
        description: Optional[str] = None,
        current_user: Optional[str] = None,
    ) -> TbToolDeploy:
        """
        Deploy tool.

        Args:
            tool_id: Tool ID
            description: Deployment description
            current_user: Current username

        Returns:
            TbToolDeploy: Tool deployment

        Raises:
            ToolNotFoundError: If tool not found
        """
        # Get tool
        tool = await self.get_tool_by_id(tool_id)
        if not tool:
            logger.error(f"Tool not found for deploy operation: {tool_id}")
            raise ToolNotFoundError(tool_id=tool_id)

        # Get next version
        version = 1
        if tool.current_version:
            version = tool.current_version + 1

        # Create deployment
        current_time = get_current_unix_ms()
        deploy = TbToolDeploy(
            tool_id=tool.id,
            version=version,
            parameters=tool.parameters,  # Already a JSON string
            code=tool.code,
            type=tool.type,
            setting=tool.setting,  # Already a JSON string
            description=description,
            created_at=current_time,
            updated_at=current_time,
            created_by=current_user,
            updated_by=current_user,
        )

        self.db.add(deploy)

        # Update tool version
        tool.current_version = version

        await self.db.commit()
        await self.db.refresh(deploy)

        return deploy

    async def get_tool_deploy_history(
        self, tool_id: int, page: int = 1, size: int = 20
    ) -> Tuple[List[TbToolDeploy], int]:
        """
        Get tool deployment history.

        Args:
            tool_id: Tool ID
            page: Page number (1-based)
            size: Page size

        Returns:
            Tuple[List[TbToolDeploy], int]: List of deployments and total count

        Raises:
            ToolNotFoundError: If tool not found
        """
        # Check if tool exists
        tool = await self.get_tool_by_id(tool_id)
        if not tool:
            logger.error(f"Tool not found for deployment history query: {tool_id}")
            raise ToolNotFoundError(tool_id=tool_id)

        # Query deployments
        query = select(TbToolDeploy).where(TbToolDeploy.tool_id == tool_id)

        # Count total
        count_result = await self.db.execute(
            select(TbToolDeploy.id).where(TbToolDeploy.tool_id == tool_id)
        )
        total = len(count_result.scalars().all())

        # Apply pagination and ordering
        query = (
            query.order_by(desc(TbToolDeploy.version))
            .offset((page - 1) * size)
            .limit(size)
        )

        # Execute query
        result = await self.db.execute(query)
        deploys = result.scalars().all()

        return list(deploys), total

    @audit(operation_type="rollback", object_type="tool")
    async def rollback_tool(
        self, tool_id: int, version: int, current_user: Optional[str] = None
    ) -> TbTool:
        """
        Rollback tool to a specific version.

        Args:
            tool_id: Tool ID
            version: Version to rollback to
            current_user: Current username

        Returns:
            TbTool: Updated tool

        Raises:
            ToolNotFoundError: If tool not found
            ToolVersionNotFoundError: If version not found
        """
        # Get tool
        tool = await self.get_tool_by_id(tool_id)
        if not tool:
            logger.error(f"Tool not found for rollback operation: {tool_id}")
            raise ToolNotFoundError(tool_id=tool_id)

        # Get deployment
        result = await self.db.execute(
            select(TbToolDeploy).where(
                TbToolDeploy.tool_id == tool_id, TbToolDeploy.version == version
            )
        )
        deploy = result.scalars().first()

        if not deploy:
            logger.error(
                f"Tool version not found for rollback operation: tool {tool_id}, version {version}"
            )
            raise ToolVersionNotFoundError(tool_id=tool_id, version=version)

        # Update tool
        tool.parameters = deploy.parameters  # Already a JSON string
        tool.code = deploy.code
        tool.updated_at = get_current_unix_ms()
        tool.updated_by = current_user

        await self.db.commit()
        await self.db.refresh(tool)

        return tool

    @audit(operation_type="update", object_type="tool")
    async def toggle_tool_state(
        self, tool_id: int, enable: bool, current_user: Optional[str] = None
    ) -> TbTool:
        """
        Enable or disable a tool.

        Args:
            tool_id: Tool ID
            enable: Whether to enable or disable the tool
            current_user: Current username

        Returns:
            TbTool: Updated tool

        Raises:
            ToolNotFoundError: If tool not found
            ToolStateChangeError: If tool state change fails
        """
        # Get tool
        tool = await self.get_tool_by_id(tool_id)
        if not tool:
            logger.error(f"Tool not found for state change operation: {tool_id}")
            raise ToolNotFoundError(tool_id=tool_id)

        # Check if state is already set
        if tool.is_enabled == enable:
            logger.warning(
                f"Tool {tool_id} is already {'enabled' if enable else 'disabled'}"
            )
            return tool

        try:
            # Update tool state
            tool.is_enabled = enable
            tool.updated_at = get_current_unix_ms()
            tool.updated_by = current_user

            await self.db.commit()
            await self.db.refresh(tool)

            logger.info(
                f"Tool {tool_id} has been {'enabled' if enable else 'disabled'} by {current_user}"
            )
            return tool
        except Exception as e:
            logger.error(
                f"Failed to {'enable' if enable else 'disable'} tool {tool_id}: {str(e)}"
            )
            raise ToolStateChangeError(tool_id=tool_id, enable=enable, error=str(e))

    @audit(operation_type="delete", object_type="tool")
    async def delete_tool(
        self, tool_id: int, current_user: Optional[str] = None
    ) -> Optional[TbTool]:
        """
        Delete tool and all related records (deployments, function associations, config associations).

        Args:
            tool_id: Tool ID
            current_user: Current username

        Returns:
            TbTool: Deleted tool or None if not found

        Raises:
            ToolNotFoundError: If tool not found
        """
        # Get tool
        tool = await self.get_tool_by_id(tool_id)
        if not tool:
            logger.error(f"Tool not found for delete operation: {tool_id}")
            raise ToolNotFoundError(tool_id=tool_id)

        # Delete related records in tb_tool_deploy
        await self.db.execute(
            TbToolDeploy.__table__.delete().where(TbToolDeploy.tool_id == tool_id)
        )

        # Delete related records in tb_tool_func
        await self.db.execute(
            TbToolFunc.__table__.delete().where(TbToolFunc.tool_id == tool_id)
        )

        # Delete related records in tb_tool_config
        await self.db.execute(
            TbToolConfig.__table__.delete().where(TbToolConfig.tool_id == tool_id)
        )

        # Delete tool
        await self.db.delete(tool)
        await self.db.commit()

        return tool

    async def get_tool_funcs(self, tool_id: int) -> List[TbFunc]:
        """
        Get functions associated with a tool.

        Args:
            tool_id: Tool ID

        Returns:
            List[TbFunc]: List of functions associated with the tool

        Raises:
            ToolNotFoundError: If tool not found
        """
        # Check if tool exists
        tool = await self.get_tool_by_id(tool_id)
        if not tool:
            logger.error(f"Tool not found for function list query: {tool_id}")
            raise ToolNotFoundError(tool_id=tool_id)

        # Get functions used by this tool
        result = await self.db.execute(
            select(TbFunc)
            .join(TbToolFunc, TbToolFunc.func_id == TbFunc.id)
            .where(TbToolFunc.tool_id == tool_id)
        )
        funcs = result.scalars().all()

        return funcs

    async def get_tool_configs(self, tool_id: int) -> List[TbConfig]:
        """
        Get configurations associated with a tool.

        Args:
            tool_id: Tool ID

        Returns:
            List[TbConfig]: List of configurations associated with the tool

        Raises:
            ToolNotFoundError: If tool not found
        """
        # Check if tool exists
        tool = await self.get_tool_by_id(tool_id)
        if not tool:
            logger.error(f"Tool not found for config list query: {tool_id}")
            raise ToolNotFoundError(tool_id=tool_id)

        # Get configurations used by this tool
        result = await self.db.execute(
            select(TbConfig)
            .join(TbToolConfig, TbToolConfig.config_id == TbConfig.id)
            .where(TbToolConfig.tool_id == tool_id)
        )
        configs = result.scalars().all()

        return configs

    async def execute_tool(
        self, tool_id: int, parameters: Dict[str, Any], call_type: str = "mcp"
    ) -> Tuple[Any, List[str]]:
        """
        Execute a tool with the given parameters.

        Args:
            tool_id: Tool ID
            parameters: Tool parameters
            call_type: Call type (mcp, debug)

        Returns:
            Tuple[Any, List[str]]: Execution result and logs

        Raises:
            ToolNotFoundError: If tool not found
            ToolExecutionError: If execution fails
        """
        # Record start time for logging
        request_time = get_current_unix_ms()
        is_success = False
        error_message = None
        result_data = None
        logs = []

        try:
            # Get tool
            tool = await self.get_tool_by_id(tool_id)
            if not tool:
                logger.error(f"Tool not found for execution: {tool_id}")
                raise ToolNotFoundError(tool_id=tool_id)

            # Get tool functions
            tool_funcs = await self.get_tool_funcs(tool_id)

            # Get function code
            func_code = {}
            for func in tool_funcs:
                func_code[func.name] = func.code

            # Get tool configs
            tool_configs = await self.get_tool_configs(tool_id)

            # Create a combined code string
            combined_code = f"""
# Function code
{"\n".join([code for code in func_code.values()])}

# Tool code
{tool.code}
"""

            # Log the combined code for debugging
            logger.debug(f"combined code:\n{combined_code}")

            # Create a namespace for execution
            namespace = {}

            # Add parameters to namespace
            namespace["parameters"] = parameters

            namespace["config"] = None
            # Add configs to namespace if available
            if tool_configs:
                config_var = {}
                for config in tool_configs:
                    if config.conf_value:
                        try:
                            config_value = json.loads(config.conf_value)
                            config_var.update(config_value)
                        except json.JSONDecodeError:
                            logger.warning(
                                f"Invalid JSON in config {config.name}: {config.conf_value}"
                            )
                            continue
                namespace["config"] = config_var

            # Execute the module code directly
            output_buffer = io.StringIO()

            try:
                with redirect_stdout(output_buffer), redirect_stderr(output_buffer):
                    exec(combined_code, namespace)
            except Exception as e:
                error_message = (
                    f"Error executing tool: {str(e)}\n{traceback.format_exc()}"
                )
                raise ToolExecutionError(tool_id=tool_id, error_message=error_message)

            # Get the output
            output = output_buffer.getvalue()

            # Process the output into logs
            if output:
                # Split the output into lines and add to logs
                logs.extend([line for line in output.strip().split("\n") if line])

            # Get the result from the namespace
            result = namespace.get("result")
            result_data = result
            is_success = True

            return result, logs

        except Exception as e:
            error_message = str(e)
            logger.error(f"Tool execution error for tool {tool_id}: {error_message}")
            raise

        finally:
            # Record tool log
            try:
                # Import here to avoid circular imports
                from api.services.tool_log_service import ToolLogService

                response_time = get_current_unix_ms()
                duration_ms = response_time - request_time

                tool_log_service = ToolLogService(self.db)
                await tool_log_service.create_log(
                    tool_name=tool.name
                    if "tool" in locals() and tool
                    else f"tool_{tool_id}",
                    call_type=call_type,
                    tool_id=tool_id,
                    request_time=request_time,
                    response_time=response_time,
                    duration_ms=duration_ms,
                    is_success=is_success,
                    error_message=error_message,
                    request_params=parameters,
                    response_data=result_data,
                )
            except Exception as log_error:
                # Log recording failure should not affect main functionality
                logger.warning(f"Failed to record tool log: {str(log_error)}")

    async def list_builtin_tools(self) -> BuiltinToolListResponse:
        """
        List all builtin tools from the sample directory.

        Returns:
            BuiltinToolListResponse: List of builtin tools
        """
        # Get the sample directory path
        sample_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample")
        if not os.path.exists(sample_dir):
            logger.warning(f"Sample directory not found: {sample_dir}")
            return BuiltinToolListResponse(tools=[])

        # Get all subdirectories in the sample directory
        tools = []
        for tool_dir in os.listdir(sample_dir):
            tool_path = os.path.join(sample_dir, tool_dir)
            if not os.path.isdir(tool_path):
                continue

            # Check if manifest.yaml exists
            manifest_path = os.path.join(tool_path, "manifest.yaml")
            if not os.path.exists(manifest_path):
                logger.warning(f"Manifest file not found in {tool_path}")
                continue

            try:
                # Read manifest.yaml
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest = yaml.safe_load(f)

                # Create tool info
                tool_info = BuiltinToolInfo(
                    id=tool_dir,
                    name=manifest.get("tool", tool_dir),
                    description=manifest.get("description", ""),
                    has_config="config" in manifest,
                )
                tools.append(tool_info)
            except Exception as e:
                logger.error(f"Error reading manifest file {manifest_path}: {str(e)}")
                continue

        return BuiltinToolListResponse(tools=tools)

    @audit(operation_type="import", object_type="tool")
    async def import_builtin_tool(
        self, tool_id: str, current_user: Optional[str] = None
    ) -> TbTool:
        """
        Import a builtin tool from the sample directory.

        Args:
            tool_id: Tool ID (directory name)
            current_user: Current username

        Returns:
            TbTool: Imported tool

        Raises:
            ToolNotFoundError: If tool not found
            ToolAlreadyExistsError: If tool already exists
        """
        # Get the sample directory path
        sample_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample")
        tool_path = os.path.join(sample_dir, tool_id)
        if not os.path.exists(tool_path) or not os.path.isdir(tool_path):
            logger.error(f"Tool directory not found: {tool_path}")
            raise ToolNotFoundError(name=tool_id)

        # Check if manifest.yaml exists
        manifest_path = os.path.join(tool_path, "manifest.yaml")
        if not os.path.exists(manifest_path):
            logger.error(f"Manifest file not found in {tool_path}")
            raise ToolNotFoundError(name=tool_id)

        try:
            # Read manifest.yaml
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = yaml.safe_load(f)

            # Get tool name
            tool_name = manifest.get("tool", tool_id)

            # Check if tool already exists
            existing_tool = await self.get_tool_by_name(tool_name)
            if existing_tool:
                logger.warning(f"Tool already exists: {tool_name}")
                raise ToolAlreadyExistsError(name=tool_name)

            # Get tool code
            code_file = manifest.get("code", {}).get("file")
            if not code_file:
                logger.error(f"Code file not specified in manifest: {manifest_path}")
                raise ToolNotFoundError(name=tool_id)

            code_path = os.path.join(tool_path, code_file)
            if not os.path.exists(code_path):
                # Try with _func suffix
                func_name = os.path.splitext(code_file)[0]
                code_path = os.path.join(tool_path, f"{func_name}_func.py")
                if not os.path.exists(code_path):
                    logger.error(f"Code file not found: {code_path}")
                    raise ToolNotFoundError(name=tool_id)

            # Read code file
            with open(code_path, "r", encoding="utf-8") as f:
                code = f.read()

            # Create tool
            tool_data = ToolCreate(
                name=tool_name,
                description=manifest.get("description", ""),
                parameters=manifest.get("parameters", {}),
                code=code,
                config_ids=[],
                func_ids=[],
            )

            # Create tool
            tool = await self.create_tool(tool_data, current_user)

            # Create config if needed
            config_id = None
            if "config" in manifest:
                # Create config service
                from api.services.config_service import ConfigService

                config_service = ConfigService(self.db)

                # Create config
                config_data = ConfigCreate(
                    name=f"{tool_name}_config",
                    description=f"Configuration for {tool_name}",
                    conf_schema=manifest.get("config", {}),
                    conf_value=None,
                )
                config = await config_service.create_config(config_data, current_user)
                config_id = config.id

                # Associate config with tool
                current_time = get_current_unix_ms()
                tool_config = TbToolConfig(
                    tool_id=tool.id,
                    config_id=config_id,
                    created_at=current_time,
                    updated_at=current_time,
                    created_by=current_user,
                    updated_by=current_user,
                )
                self.db.add(tool_config)
                await self.db.commit()

            # Deploy tool
            await self.deploy_tool(tool.id, "Initial import", current_user)

            # Refresh tool
            await self.db.refresh(tool)

            return tool

        except (ToolNotFoundError, ToolAlreadyExistsError):
            raise
        except Exception as e:
            logger.error(f"Error importing tool {tool_id}: {str(e)}")
            raise ToolNotFoundError(name=tool_id)

"""
Tool service.
"""

import io
import json
import logging
import traceback
from contextlib import redirect_stdout, redirect_stderr
from typing import Optional, List, Tuple, Dict, Any

from sqlalchemy import or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from api.errors.tool_error import (
    ToolNotFoundError,
    ToolAlreadyExistsError,
    ToolVersionNotFoundError,
    ToolExecutionError,
)
from api.models.tb_config import TbConfig
from api.models.tb_func import TbFunc
from api.models.tb_tool import TbTool, TbToolDeploy, TbToolFunc, TbToolConfig
from api.schemas.tool_schema import ToolCreate, ToolUpdate
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
        count_result = await self.db.execute(
            select(TbTool.id).where(query.whereclause)
            if query.whereclause
            else select(TbTool.id)
        )
        total = len(count_result.scalars().all())

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

        # Create tool
        current_time = get_current_unix_ms()
        tool = TbTool(
            name=tool_data.name,
            description=tool_data.description,
            parameters=json.dumps(tool_data.parameters),
            code=tool_data.code,
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
        self, tool_id: int, parameters: Dict[str, Any]
    ) -> Tuple[Any, List[str]]:
        """
        Execute a tool with the given parameters.

        Args:
            tool_id: Tool ID
            parameters: Tool parameters

        Returns:
            Tuple[Any, List[str]]: Execution result and logs

        Raises:
            ToolNotFoundError: If tool not found
            ToolExecutionError: If execution fails
        """
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

        # Get config values
        config_values = {}
        for conf in tool_configs:
            if conf.conf_value:
                try:
                    conf_value_dic = json.loads(conf.conf_value)
                    config_values.update(conf_value_dic)
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"Error loading config {conf.name}: Invalid JSON")

        # Prepare the combined code
        combined_code = f"""# Global variables
parameters = {repr(parameters)}
config = {repr(config_values)}
result = None

# Dependent functions
{"\n".join([code for code in func_code.values()])}

# Tool code
{tool.code}
"""

        # Log the combined code for debugging
        logger.debug(f"combined code:\n{combined_code}")

        # Create a namespace for execution
        namespace = {}

        # Execute the module code directly
        output_buffer = io.StringIO()
        error_message = None

        try:
            with redirect_stdout(output_buffer), redirect_stderr(output_buffer):
                exec(combined_code, namespace)
        except Exception as e:
            error_message = f"Error executing tool: {str(e)}\n{traceback.format_exc()}"

        # Get the output
        output = output_buffer.getvalue()

        # Process the output into logs
        logs = []
        if output:
            # Split the output into lines and add to logs
            logs.extend([line for line in output.strip().split("\n") if line])

        # Handle execution errors
        if error_message:
            logs.append(error_message)
            logger.error(f"Tool execution error for tool {tool_id}: {error_message}")
            raise ToolExecutionError(tool_id=tool_id, error_message=error_message)

        # Get the result from the namespace
        result = namespace.get("result")

        return result, logs

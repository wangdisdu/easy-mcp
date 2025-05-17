"""
Configuration service.
"""

import json
from typing import Optional, List, Tuple

from sqlalchemy import or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from api.errors.config_error import (
    ConfigNotFoundError,
    ConfigAlreadyExistsError,
    ConfigInUseError,
)
from api.models.tb_config import TbConfig
from api.models.tb_tool import TbTool, TbToolConfig
from api.schemas.config_schema import ConfigCreate, ConfigUpdate
from api.schemas.usage_schema import ConfigUsageResponse
from api.utils.audit_util import audit
from api.utils.time_util import get_current_unix_ms


class ConfigService:
    """
    Configuration service.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize configuration service.

        Args:
            db: Database session
        """
        self.db = db

    async def get_config_by_id(self, config_id: int) -> Optional[TbConfig]:
        """
        Get configuration by ID.

        Args:
            config_id: Configuration ID

        Returns:
            TbConfig: Configuration object or None if not found
        """
        result = await self.db.execute(select(TbConfig).where(TbConfig.id == config_id))
        return result.scalars().first()

    async def get_config_by_name(self, name: str) -> Optional[TbConfig]:
        """
        Get configuration by name.

        Args:
            name: Configuration name

        Returns:
            TbConfig: Configuration object or None if not found
        """
        result = await self.db.execute(select(TbConfig).where(TbConfig.name == name))
        return result.scalars().first()

    async def query_configs(
        self, page: int = 1, size: int = 20, search: Optional[str] = None
    ) -> Tuple[List[TbConfig], int]:
        """
        Query configurations with pagination.

        Args:
            page: Page number (1-based)
            size: Page size
            search: Search term for name or description

        Returns:
            Tuple[List[TbConfig], int]: List of configurations and total count
        """
        query = select(TbConfig)

        # Apply filters
        if search:
            query = query.where(
                or_(
                    TbConfig.name.ilike(f"%{search}%"),
                    TbConfig.description.ilike(f"%{search}%"),
                )
            )

        # Count total
        count_result = await self.db.execute(
            select(TbConfig.id).where(query.whereclause)
            if query.whereclause
            else select(TbConfig.id)
        )
        total = len(count_result.scalars().all())

        # Apply pagination and ordering
        query = query.order_by(desc(TbConfig.id)).offset((page - 1) * size).limit(size)

        # Execute query
        result = await self.db.execute(query)
        configs = result.scalars().all()

        return list(configs), total

    @audit(operation_type="create", object_type="config")
    async def create_config(
        self, config_data: ConfigCreate, current_user: Optional[str] = None
    ) -> TbConfig:
        """
        Create a new configuration.

        Args:
            config_data: Configuration data
            current_user: Current username

        Returns:
            TbConfig: Created configuration

        Raises:
            ConfigAlreadyExistsError: If configuration already exists
        """
        # Check if configuration already exists
        existing_config = await self.get_config_by_name(config_data.name)
        if existing_config:
            raise ConfigAlreadyExistsError(name=config_data.name)

        # Create configuration
        current_time = get_current_unix_ms()
        config = TbConfig(
            name=config_data.name,
            description=config_data.description,
            conf_schema=json.dumps(config_data.conf_schema),
            conf_value=json.dumps(config_data.conf_value)
            if config_data.conf_value
            else None,
            created_at=current_time,
            updated_at=current_time,
            created_by=current_user,
            updated_by=current_user,
        )

        self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)

        return config

    @audit(operation_type="update", object_type="config")
    async def update_config(
        self,
        config_id: int,
        config_data: ConfigUpdate,
        current_user: Optional[str] = None,
    ) -> Optional[TbConfig]:
        """
        Update configuration.

        Args:
            config_id: Configuration ID
            config_data: Configuration data
            current_user: Current username

        Returns:
            TbConfig: Updated configuration or None if not found

        Raises:
            ConfigNotFoundError: If configuration not found
            ConfigAlreadyExistsError: If configuration name already exists
        """
        # Get configuration
        config = await self.get_config_by_id(config_id)
        if not config:
            raise ConfigNotFoundError(config_id=config_id)

        # Check if name already exists
        if config_data.name != config.name:
            existing_config = await self.get_config_by_name(config_data.name)
            if existing_config:
                raise ConfigAlreadyExistsError(name=config_data.name)

        # Update configuration
        config.name = config_data.name
        config.description = config_data.description
        config.conf_schema = json.dumps(config_data.conf_schema)

        if config_data.conf_value is not None:
            config.conf_value = json.dumps(config_data.conf_value)

        config.updated_at = get_current_unix_ms()
        config.updated_by = current_user

        await self.db.commit()
        await self.db.refresh(config)

        return config

    async def check_config_in_use(self, config_id: int) -> Tuple[bool, List[dict]]:
        """
        Check if configuration is in use.

        Args:
            config_id: Configuration ID

        Returns:
            Tuple[bool, List[dict]]: Is in use, tools using it
        """
        # Check if used by tools
        result = await self.db.execute(
            select(TbToolConfig).where(TbToolConfig.config_id == config_id)
        )
        tool_configs = result.scalars().all()

        # Get tool details
        tools_using = []
        for tool_config in tool_configs:
            result = await self.db.execute(
                select(TbConfig).where(TbConfig.id == tool_config.tool_id)
            )
            tool = result.scalars().first()
            if tool:
                tools_using.append({"id": tool.id, "name": tool.name})

        is_in_use = len(tools_using) > 0

        return is_in_use, tools_using

    @audit(operation_type="delete", object_type="config")
    async def delete_config(
        self, config_id: int, current_user: Optional[str] = None
    ) -> Optional[TbConfig]:
        """
        Delete configuration.

        Args:
            config_id: Configuration ID
            current_user: Current username

        Returns:
            TbConfig: Deleted configuration or None if not found

        Raises:
            ConfigNotFoundError: If configuration not found
            ConfigInUseError: If configuration is in use
        """
        # Get configuration
        config = await self.get_config_by_id(config_id)
        if not config:
            raise ConfigNotFoundError(config_id=config_id)

        # Check if configuration is in use
        is_in_use, tools_using = await self.check_config_in_use(config_id)
        if is_in_use:
            raise ConfigInUseError(config_id=config_id, used_by_tools=tools_using)

        # Delete configuration
        await self.db.delete(config)
        await self.db.commit()

        return config

    async def get_config_usage(self, config_id: int) -> ConfigUsageResponse:
        """
        Get usage information for a configuration.

        Args:
            config_id: Configuration ID

        Returns:
            ConfigUsageResponse: Usage information for the configuration

        Raises:
            ConfigNotFoundError: If configuration not found
        """
        # Check if configuration exists
        config = await self.get_config_by_id(config_id)
        if not config:
            raise ConfigNotFoundError(config_id=config_id)

        # Get tools using this configuration
        result = await self.db.execute(
            select(TbTool)
            .join(TbToolConfig, TbToolConfig.tool_id == TbTool.id)
            .where(TbToolConfig.config_id == config_id)
        )
        tools = result.scalars().all()

        # Create response
        from api.schemas.tool_schema import ToolResponse

        tool_responses = [ToolResponse.model_validate(tool) for tool in tools]

        return ConfigUsageResponse(tools=tool_responses)

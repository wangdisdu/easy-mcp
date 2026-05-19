"""
MCP service for handling MCP protocol operations.

This service provides a reusable interface for MCP operations including
tool listing and execution, with support for tag-based filtering.
"""

import json
import logging
from typing import Dict, Any, List, Optional

import mcp.types as types
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.tag_service import TagService
from api.services.tool_service import ToolService

# Create logger
logger = logging.getLogger(__name__)


class MCPService:
    """
    MCP service for handling MCP protocol operations.
    
    This service provides a reusable interface for MCP operations including
    tool listing and execution, with support for tag-based filtering.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize MCP service with database session.

        Args:
            db: Database session for this service instance
        """
        self.db = db
        self._tool_service = ToolService(db)

    async def list_tools(
        self,
        tag_filter: Optional[str] = None,
        allowed_tool_ids: Optional[List[int]] = None,
    ) -> List[types.Tool]:
        """
        Get all enabled tools from database and convert to MCP Tool format.

        Args:
            tag_filter: Optional tag name to filter tools by
            allowed_tool_ids: Token scope. ``None`` means no restriction; an
                empty list means the token is authorized for no tools.

        Returns:
            List of MCP Tool objects for enabled tools
        """
        try:
            # Get tag IDs if tag_filter is provided
            tag_ids = await self._get_tag_ids(tag_filter) if tag_filter else None
            if tag_filter and tag_ids is None:
                return []  # Tag not found

            # Get all tools using pagination
            all_tools = await self._get_all_tools_paginated(
                tag_ids, allowed_tool_ids
            )

            # Convert enabled tools to MCP format
            mcp_tools = self._convert_tools_to_mcp_format(all_tools)

            # Log results
            self._log_tool_loading_results(mcp_tools, all_tools, tag_filter)

            return mcp_tools

        except Exception as e:
            logger.error(f"Error getting enabled tools: {e}")
            return []

    async def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any],
        allowed_tool_ids: Optional[List[int]] = None,
    ) -> List[types.TextContent]:
        """
        Execute a tool by name with given arguments.

        Args:
            name: Tool name to execute
            arguments: Tool execution arguments
            allowed_tool_ids: Token scope. ``None`` means no restriction; the
                tool is rejected unless its ID is in this list otherwise.

        Returns:
            List of TextContent with execution results
        """
        try:
            # Get tool by name
            tool = await self._tool_service.get_tool_by_name(name)
            if not tool:
                return [self._create_error_response(f"Tool '{name}' not found")]

            # Enforce token scope: deny tools not authorized for this token.
            if allowed_tool_ids is not None and tool.id not in allowed_tool_ids:
                return [
                    self._create_error_response(
                        f"Tool '{name}' is not authorized for this token"
                    )
                ]

            if not tool.is_enabled:
                return [self._create_error_response(f"Tool '{name}' is disabled")]

            # Get incoming request headers from the request context if available.
            # These are used only as the data source for ${header["xxx"]}
            # substitution in HTTP tool header settings; they are never exposed
            # to tool code.
            request_headers = {}
            try:
                from mcp.server.lowlevel.server import request_ctx
                ctx = request_ctx.get()
                if ctx and ctx.request and hasattr(ctx.request, 'headers'):
                    request_headers = dict(ctx.request.headers)
            except Exception:
                # If we can't get headers, continue without them
                pass

            # Execute tool
            result, logs = await self._tool_service.execute_tool(
                tool.id, arguments, call_type="mcp", request_headers=request_headers
            )

            # Format and return result
            result_text = self._format_execution_result(result)
            return [types.TextContent(type="text", text=result_text)]

        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            return [self._create_error_response(f"Error executing tool: {str(e)}")]

    async def _get_tag_ids(self, tag_filter: str) -> Optional[List[int]]:
        """
        Get tag IDs for the given tag filter.

        Args:
            tag_filter: Tag name to filter by

        Returns:
            List of tag IDs or None if tag not found
        """
        tag_service = TagService(self.db)
        tag = await tag_service.get_tag_by_name(tag_filter)
        if tag:
            logger.info(f"Filtering tools by tag: {tag_filter} (ID: {tag.id})")
            return [tag.id]
        else:
            logger.warning(f"Tag not found: {tag_filter}")
            return None

    async def _get_all_tools_paginated(
        self,
        tag_ids: Optional[List[int]],
        tool_ids: Optional[List[int]] = None,
    ) -> List:
        """
        Get all tools using pagination to handle large datasets.

        Args:
            tag_ids: Optional list of tag IDs to filter by
            tool_ids: Optional token scope of allowed tool IDs

        Returns:
            List of all tools from database
        """
        all_tools = []
        page = 1

        while True:
            tools, total = await self._tool_service.query_tools(
                page=page,
                size=100,
                tag_ids=tag_ids,
                tool_ids=tool_ids,
            )

            if not tools:
                break

            all_tools.extend(tools)

            # Check if we've got all tools
            if len(all_tools) >= total:
                break

            page += 1

        return all_tools

    def _convert_tools_to_mcp_format(self, tools: List) -> List[types.Tool]:
        """
        Convert database tools to MCP Tool format, filtering enabled tools only.

        Args:
            tools: List of database tool objects

        Returns:
            List of MCP Tool objects
        """
        mcp_tools = []

        for tool in tools:
            if not tool.is_enabled:
                continue

            try:
                # Parse parameters JSON Schema
                parameters = self._parse_tool_parameters(tool.parameters)

                mcp_tool = types.Tool(
                    name=tool.name,
                    description=tool.description or "",
                    inputSchema=parameters,
                )
                mcp_tools.append(mcp_tool)

            except Exception as e:
                logger.error(f"Error converting tool {tool.name}: {e}")
                continue

        return mcp_tools

    def _parse_tool_parameters(self, parameters_str: Optional[str]) -> Dict[str, Any]:
        """
        Parse tool parameters JSON string.

        Args:
            parameters_str: JSON string of parameters

        Returns:
            Parsed parameters dictionary
        """
        if not parameters_str:
            return {}

        try:
            return json.loads(parameters_str)
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in tool parameters: {e}")
            return {}

    def _log_tool_loading_results(self, mcp_tools: List[types.Tool], all_tools: List, tag_filter: Optional[str]):
        """
        Log the results of tool loading.

        Args:
            mcp_tools: List of converted MCP tools
            all_tools: List of all tools from database
            tag_filter: Optional tag filter used
        """
        if tag_filter:
            logger.info(
                f"Loaded {len(mcp_tools)} enabled tools for tag '{tag_filter}' "
                f"(total: {len(all_tools)})"
            )
        else:
            logger.info(f"Loaded {len(mcp_tools)} enabled tools (total: {len(all_tools)})")

    def _create_error_response(self, error_message: str) -> types.TextContent:
        """
        Create an error response in TextContent format.

        Args:
            error_message: Error message to include

        Returns:
            TextContent with error message
        """
        return types.TextContent(type="text", text=f"Error: {error_message}")

    def _format_execution_result(self, result: Any) -> str:
        """
        Format tool execution result for display.

        Args:
            result: Tool execution result

        Returns:
            Formatted result string
        """
        if result is None:
            return "Tool executed successfully (no output)"
        
        if isinstance(result, str):
            return result
        
        try:
            return json.dumps(result, indent=2, ensure_ascii=False)
        except (TypeError, ValueError):
            return str(result)

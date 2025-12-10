"""
MCP Streamable HTTP router for FastAPI using StreamableHTTPSessionManager.

This module provides Streamable HTTP endpoints for the Model Context Protocol (MCP).
It supports both general tool listing and tag-filtered tool listing with session management.

Features:
- Session-based design with StreamableHTTPSessionManager
- Automatic pagination for large tool sets
- Tag-based tool filtering
- Comprehensive error handling and logging
- Streamable HTTP session management for better performance
- Stateless session management for scalability
"""

import logging
from contextvars import ContextVar
from typing import Dict, Any, List

import mcp.types as types
from fastapi import APIRouter, Request, Depends
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db, get_session
from api.services.mcp_service import MCPService

# Create logger
logger = logging.getLogger(__name__)

# Create FastAPI router
router = APIRouter(tags=["mcp-stream"])

# Initialize MCP server
mcp_stream_server = Server("Easy MCP Streamable HTTP Server")

# Initialize session manager with proper parameters
# Note: Session manager lifecycle is managed in main.py lifespan
mcp_stream_session_manager = StreamableHTTPSessionManager(
    app=mcp_stream_server,
    event_store=None,
    stateless=True,
)

# Context variables for database and tag filtering
_db_ctx = ContextVar("mcp_stream_db_ctx")
_tag_ctx = ContextVar("mcp_stream_tag_ctx", default=None)


@mcp_stream_server.list_tools()
async def list_tools() -> List[types.Tool]:
    """List available tools for this connection."""
    # Access context variables
    # 注意：这里不再直接使用_db_ctx中的数据库会话
    # 而是在需要时创建临时会话
    tag = _tag_ctx.get(None)
    
    # 创建临时数据库会话
    async with get_session() as db:
        service = MCPService(db)
        return await service.list_tools(tag)


@mcp_stream_server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool execution for this connection."""
    # 注意：这里不再直接使用_db_ctx中的数据库会话
    # 而是在需要时创建临时会话
    
    # 创建临时数据库会话
    async with get_session() as db:
        service = MCPService(db)
        return await service.call_tool(name, arguments)


async def _handle_request(request: Request):
    """
    Handle Streamable HTTP connection using StreamableHTTPSessionManager.

    This is a helper function to reduce code duplication between
    the general and tag-filtered stream endpoints.

    Args:
        request: FastAPI request object
    """
    try:
        # Use session manager to handle the request directly
        await mcp_stream_session_manager.handle_request(
            request.scope,
            request.receive,
            request._send
        )
    except Exception as e:
        logger.error(f"Error handling stream connection: {e}")
        raise


# FastAPI endpoints
@router.post("/mcp")
async def handle_stream_endpoint(
    request: Request,
):
    """
    Handle Streamable HTTP connection for MCP without tag filtering.
    
    This endpoint provides access to all enabled tools in the system.
    Uses StreamableHTTPSessionManager for session management.
    
    Args:
        request: FastAPI request object
    """
    # 不再需要设置数据库上下文，因为我们会在需要时创建临时会话
    _tag_ctx.set(None)
    
    # Handle stream connection
    await _handle_request(request)


@router.post("/mcp-{tag}")
async def handle_stream_endpoint_with_tag(
    tag: str,
    request: Request,
):
    """
    Handle Streamable HTTP connection for MCP with tag filtering.
    
    This endpoint provides access to tools filtered by a specific tag.
    If the tag doesn't exist, an empty tool list will be returned.
    Uses StreamableHTTPSessionManager for session management.
    
    Args:
        tag: Tag name to filter tools by
        request: FastAPI request object
    """
    # 不再需要设置数据库上下文，因为我们会在需要时创建临时会话
    _tag_ctx.set(tag)
    
    # Handle stream connection
    await _handle_request(request)
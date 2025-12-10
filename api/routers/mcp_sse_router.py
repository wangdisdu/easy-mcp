"""
MCP SSE router for FastAPI using transport-based implementation.

This module provides Server-Sent Events (SSE) endpoints for the Model Context Protocol (MCP).
It supports both general tool listing and tag-filtered tool listing with concurrent-safe design.

Features:
- Concurrent-safe design with per-connection handlers
- Automatic pagination for large tool sets
- Tag-based tool filtering
- Comprehensive error handling and logging
"""

import logging
from contextvars import ContextVar
from typing import Dict, Any, List

import mcp.types as types
from fastapi import APIRouter, Request, Depends, BackgroundTasks
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db, get_session
from api.services.mcp_service import MCPService

# Create logger
logger = logging.getLogger(__name__)

# Create FastAPI router
router = APIRouter(tags=["mcp-sse"])

# Initialize MCP transport
mcp_sse_transport = SseServerTransport("/messages/")

# Initialize MCP server
mcp_sse_server = Server("Easy MCP SSE Server")

_db_ctx = ContextVar("mcp_sse_db_ctx")
_tag_ctx = ContextVar("mcp_sse_tag_ctx", default=None)


@mcp_sse_server.list_tools()
async def list_tools() -> List[types.Tool]:
    """List available tools for this connection."""
    # Access lifespan context
    # 注意：这里不再直接使用_db_ctx中的数据库会话
    # 而是在需要时创建临时会话
    tag = _tag_ctx.get(None)
    
    # 创建临时数据库会话
    async with get_session() as db:
        service = MCPService(db)
        return await service.list_tools(tag)


@mcp_sse_server.call_tool()
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
    Handle SSE connection with the given MCP server.

    This is a helper function to reduce code duplication between
    the general and tag-filtered SSE endpoints.

    Args:
        request: FastAPI request object
    """
    async with mcp_sse_transport.connect_sse(
            request.scope,
            request.receive,
            request._send
    ) as streams:
        # Run the MCP server with the streams
        await mcp_sse_server.run(
            streams[0],  # read stream
            streams[1],  # write stream
            mcp_sse_server.create_initialization_options(),
        )


# FastAPI endpoints
@router.get("/sse")
async def handle_sse_endpoint(
    request: Request,
):
    """
    Handle SSE connection for MCP without tag filtering.
    
    This endpoint provides access to all enabled tools in the system.
    Each connection gets its own handler and server instance for concurrent safety.
    
    Args:
        request: FastAPI request object
    """
    # 不再需要设置数据库上下文，因为我们会在需要时创建临时会话
    _tag_ctx.set(None)
    
    # Handle SSE connection
    await _handle_request(request)


@router.get("/sse-{tag}")
async def handle_sse_endpoint_with_tag(
    tag: str,
    request: Request,
):
    """
    Handle SSE connection for MCP with tag filtering.
    
    This endpoint provides access to tools filtered by a specific tag.
    If the tag doesn't exist, an empty tool list will be returned.
    
    Args:
        tag: Tag name to filter tools by
        request: FastAPI request object
    """
    # 不再需要设置数据库上下文，因为我们会在需要时创建临时会话
    _tag_ctx.set(tag)
    
    # Handle SSE connection
    await _handle_request(request)


@router.post("/messages/{path:path}")
async def handle_post_messages(
    request: Request,
):
    """
    Handle POST messages for MCP.
    
    This endpoint handles MCP protocol messages sent via POST requests.
    It's part of the MCP transport layer implementation.
    
    Args:
        request: FastAPI request object
    """
    # 不再需要设置数据库上下文
    
    # Use the transport's handle_post_message ASGI application
    await mcp_sse_transport.handle_post_message(
        request.scope,
        request.receive,
        request._send
    )

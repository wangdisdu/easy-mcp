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
from fastapi import APIRouter, Request, Depends
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport

from api.database import get_session
from api.services.mcp_service import MCPService
from api.utils.mcp_auth import McpAuthScope, verify_mcp_token

# Create logger
logger = logging.getLogger(__name__)

# Create FastAPI router
router = APIRouter(tags=["mcp-sse"])

# Initialize MCP transport
mcp_sse_transport = SseServerTransport("/messages/")

# Initialize MCP server
mcp_sse_server = Server("Easy MCP SSE Server")

_tag_ctx = ContextVar("mcp_sse_tag_ctx", default=None)
# Token-scoped allowed tool IDs for the current connection.
_allowed_tools_ctx = ContextVar("mcp_sse_allowed_tools_ctx", default=None)


@mcp_sse_server.list_tools()
async def list_tools() -> List[types.Tool]:
    """List available tools for this connection."""
    tag = _tag_ctx.get(None)
    allowed_tool_ids = _allowed_tools_ctx.get(None)

    # 创建临时数据库会话
    async with get_session() as db:
        service = MCPService(db)
        return await service.list_tools(tag, allowed_tool_ids)


@mcp_sse_server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool execution for this connection."""
    allowed_tool_ids = _allowed_tools_ctx.get(None)

    # 创建临时数据库会话
    async with get_session() as db:
        service = MCPService(db)
        return await service.call_tool(name, arguments, allowed_tool_ids)


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
    scope: McpAuthScope = Depends(verify_mcp_token),
):
    """
    Handle SSE connection for MCP without tag filtering.

    Requires a valid MCP access token. Tools are scoped to those associated
    with the token.

    Args:
        request: FastAPI request object
        scope: Authenticated token scope
    """
    _tag_ctx.set(None)
    _allowed_tools_ctx.set(scope.allowed_tool_ids)

    # Handle SSE connection
    await _handle_request(request)


@router.get("/sse-{tag}")
async def handle_sse_endpoint_with_tag(
    tag: str,
    request: Request,
    scope: McpAuthScope = Depends(verify_mcp_token),
):
    """
    Handle SSE connection for MCP with tag filtering.

    Requires a valid MCP access token. Returned tools are the intersection of
    the tag filter and the token's associated tools.

    Args:
        tag: Tag name to filter tools by
        request: FastAPI request object
        scope: Authenticated token scope
    """
    _tag_ctx.set(tag)
    _allowed_tools_ctx.set(scope.allowed_tool_ids)

    # Handle SSE connection
    await _handle_request(request)


@router.post("/messages/{path:path}")
async def handle_post_messages(
    request: Request,
    scope: McpAuthScope = Depends(verify_mcp_token),
):
    """
    Handle POST messages for MCP.

    Requires a valid MCP access token. This is the client->server channel of
    the SSE transport.

    Args:
        request: FastAPI request object
        scope: Authenticated token scope
    """
    # Use the transport's handle_post_message ASGI application
    await mcp_sse_transport.handle_post_message(
        request.scope,
        request.receive,
        request._send
    )

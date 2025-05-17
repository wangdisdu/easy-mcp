"""
MCP router.
"""

import asyncio
import json
import logging
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from api.database import get_db
from api.models.tb_tool import TbTool
from api.services.tool_service import ToolService

# Create logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["mcp"])


async def get_tools(db: AsyncSession) -> List[Dict[str, Any]]:
    """
    Get all enabled tools.

    Args:
        db: Database session

    Returns:
        List[Dict[str, Any]]: List of tools
    """
    result = await db.execute(select(TbTool).where(TbTool.is_enabled == True))
    tools = result.scalars().all()

    tool_list = []
    for tool in tools:
        tool_list.append(
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
                "id": tool.id,
            }
        )

    return tool_list


async def sse_generator(request: Request, db: AsyncSession):
    """
    Server-Sent Events generator.

    Args:
        request: Request object
        db: Database session

    Yields:
        str: SSE data
    """
    # Send initial tools list
    tools = await get_tools(db)
    yield f"data: {json.dumps({'tools': tools})}\n\n"

    # Keep connection alive
    while True:
        if await request.is_disconnected():
            logger.info("Client disconnected")
            break

        # Wait for a while
        await asyncio.sleep(30)

        # Send heartbeat
        yield f"data: {json.dumps({'heartbeat': True})}\n\n"


@router.get("/sse")
async def sse_endpoint(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Server-Sent Events endpoint.

    Args:
        request: Request object
        db: Database session

    Returns:
        StreamingResponse: SSE response
    """
    return StreamingResponse(sse_generator(request, db), media_type="text/event-stream")


@router.post("/invoke/{tool_id}")
async def invoke_tool(
    tool_id: int, parameters: Dict[str, Any], db: AsyncSession = Depends(get_db)
):
    """
    Invoke tool.

    Args:
        tool_id: Tool ID
        parameters: Tool parameters
        db: Database session

    Returns:
        Dict[str, Any]: Tool result
    """
    service = ToolService(db)
    result, logs = await service.debug_tool(tool_id, parameters)

    return {"result": result, "logs": logs}

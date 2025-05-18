"""
MCP router.
"""

import json
import logging
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional, Tuple

from fastapi import APIRouter, Depends, Request as FastAPIRequest
from fastapi.responses import Response
from mcp.server.lowlevel import Server as McpServer
from mcp.server.sse import SseServerTransport
from mcp.types import TextContent
from mcp.types import Tool as McpTool
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.errors.mcp_error import McpMessageHandlingError, McpToolExecutionError
from api.errors.tool_error import ToolNotFoundError
from api.services.func_service import FuncService
from api.services.tool_service import ToolService


# Create logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["mcp"])


class McpServerManager:
    """MCP 服务器管理类，负责初始化和管理 MCP 服务器及 SSE 传输"""

    def __init__(self):
        self.server: Optional[McpServer] = None
        self.transport: Optional[SseServerTransport] = None

    def initialize(self):
        """初始化 MCP 服务器和 SSE 传输

        注意：工具列表和执行函数将在 handle_sse 中注册，
        以便能够访问数据库会话
        """
        logger.info("初始化 MCP 服务器...")
        self.server = McpServer("Easy MCP Server")
        self.transport = SseServerTransport("/messages/")

        # 注意：工具列表和执行函数将在 handle_sse 中注册
        # 这里不注册是因为我们需要数据库会话

        logger.info("MCP 服务器初始化成功")

    def shutdown(self):
        """关闭 MCP 服务器"""
        logger.info("关闭 MCP 服务器...")
        # 这里可以添加任何必要的清理代码
        self.server = None
        self.transport = None

    async def _get_enabled_tools(self, db: AsyncSession) -> List[McpTool]:
        """获取所有启用的工具并转换为 MCP 工具格式

        Args:
            db: 数据库会话

        Returns:
            List[McpTool]: MCP 工具列表
        """
        tool_service = ToolService(db)
        tools = await tool_service.query_tools(page=1, size=1000)

        # 获取所有工具（第一个元素是工具列表，第二个是总数）
        all_tools = tools[0]

        # 过滤启用的工具
        enabled_tools = [tool for tool in all_tools if tool.is_enabled]

        # 转换为 MCP 工具对象
        mcp_tools = []
        for tool in enabled_tools:
            mcp_tool = self._convert_to_mcp_tool(tool)
            if mcp_tool:
                mcp_tools.append(mcp_tool)

        logger.info(f"为 MCP SSE 服务器列出 {len(mcp_tools)} 个启用的工具")
        return mcp_tools

    def _convert_to_mcp_tool(self, tool) -> Optional[McpTool]:
        """将数据库工具对象转换为 MCP 工具对象

        Args:
            tool: 数据库工具对象

        Returns:
            Optional[McpTool]: MCP 工具对象，如果转换失败则返回 None
        """
        # 解析参数
        parameters = {}
        if tool.parameters:
            try:
                parameters = json.loads(tool.parameters)
            except json.JSONDecodeError:
                logger.warning(f"无法解析工具 {tool.name} 的参数")
                return None

        # 创建 MCP 工具
        return McpTool(
            name=tool.name, description=tool.description or "", inputSchema=parameters
        )

    async def _execute_tool(
        self, name: str, arguments: Dict[str, Any], db: AsyncSession
    ) -> List[TextContent]:
        """通过名称和参数调用工具

        Args:
            name: 工具名称
            arguments: 工具参数
            db: 数据库会话

        Returns:
            List[TextContent]: 工具执行结果
        """
        logger.info(f"MCP 服务器: 调用工具: {name}, 参数: {arguments}")

        try:
            result, logs = await self._process_tool_execution(name, arguments, db)

            # 转换结果为字符串
            result_str = self._format_result(result)
            logger.info(f"成功执行工具 '{name}' 结果为: '{result_str}'")

            # 如果有日志输出，记录并包含在响应中
            if logs:
                log_str = "\n".join(logs)
                logger.info(f"工具 '{name}' 执行日志: {log_str}")

                # 尝试将结果和日志作为 JSON 返回
                try:
                    # 如果结果是字典或可以解析为字典
                    if isinstance(result, dict):
                        result_dict = result
                    else:
                        try:
                            result_dict = json.loads(result_str)
                            if not isinstance(result_dict, dict):
                                result_dict = {"result": result_str}
                        except json.JSONDecodeError:
                            result_dict = {"result": result_str}

                    return [
                        TextContent(
                            type="text",
                            text=json.dumps(result_dict, ensure_ascii=False),
                        )
                    ]
                except Exception as e:
                    logger.warning(f"将结果和日志组合为 JSON 时出错: {str(e)}")

            # 如果没有日志或组合失败，只返回结果
            return [TextContent(type="text", text=result_str)]

        except Exception as e:
            error_message = str(e)
            logger.error(f"执行工具 '{name}' 出错: {error_message}")
            error_response = {"error": error_message}
            return [TextContent(text=json.dumps(error_response, ensure_ascii=False))]

    async def _process_tool_execution(
        self, name: str, arguments: Dict[str, Any], db: AsyncSession
    ) -> Tuple[Any, List[str]]:
        """处理工具执行逻辑

        Args:
            name: 工具名称
            arguments: 工具参数
            db: 数据库会话

        Returns:
            Tuple[Any, List[str]]: 执行结果和日志

        Raises:
            ToolNotFoundError: 如果找不到工具
            McpToolExecutionError: 如果工具执行失败
        """
        tool_service = ToolService(db)

        # 获取工具
        tool = await tool_service.get_tool_by_name(name)
        if not tool:
            logger.error(f"找不到工具 '{name}'")
            raise ToolNotFoundError(name=name)

        if not tool.is_enabled:
            logger.error(f"工具 '{name}' 已禁用")
            raise McpToolExecutionError(tool_name=name, error_message="工具已禁用")

        # 执行工具
        try:
            result, logs = await tool_service.execute_tool(tool.id, arguments)
            return result, logs
        except Exception as e:
            logger.error(f"执行工具 '{name}' 时发生错误: {str(e)}")
            raise McpToolExecutionError(tool_name=name, error_message=str(e))

    def _format_result(self, result: Any) -> str:
        """格式化结果为字符串"""
        if isinstance(result, (dict, list)):
            return json.dumps(result, ensure_ascii=False)
        return str(result)


# 创建全局 MCP 服务器管理器实例
mcp_manager = McpServerManager()


# MCP 服务器生命周期管理
@asynccontextmanager
async def mcp_server_lifespan():
    """MCP 服务器生命周期上下文管理器"""
    # 初始化服务器
    mcp_manager.initialize()
    yield
    # 关闭服务器
    mcp_manager.shutdown()


# 依赖项：获取 MCP 服务器
def get_mcp_server():
    """获取 MCP 服务器实例"""
    if mcp_manager.server is None:
        raise RuntimeError("MCP 服务器未初始化")
    return mcp_manager.server


# 依赖项：获取 SSE 传输
def get_sse_transport():
    """获取 SSE 传输实例"""
    if mcp_manager.transport is None:
        raise RuntimeError("SSE 传输未初始化")
    return mcp_manager.transport


# SSE 连接处理
async def handle_sse(request: FastAPIRequest, db: AsyncSession = Depends(get_db)):
    """处理 SSE 连接

    Args:
        request: FastAPI 请求对象
        db: 数据库会话

    Returns:
        Response: 响应对象
    """
    try:
        logger.info("处理新的 SSE 连接")
        # 获取 MCP 服务器和传输
        server = get_mcp_server()
        transport = get_sse_transport()

        # 注册工具列表函数（使用闭包捕获数据库会话）
        async def list_tools_with_db():
            return await mcp_manager._get_enabled_tools(db)

        # 注册工具执行函数（使用闭包捕获数据库会话）
        async def execute_tool_with_db(name: str, arguments: Dict[str, Any]):
            return await mcp_manager._execute_tool(name, arguments, db)

        # 重新注册工具列表和执行函数
        server.list_tools()(list_tools_with_db)
        server.call_tool()(execute_tool_with_db)

        # 连接到 SSE
        async with transport.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            # 运行 MCP 应用
            await server.run(
                streams[0], streams[1], server.create_initialization_options()
            )
        return Response()
    except Exception as e:
        logger.error(f"处理 SSE 连接时出错: {str(e)}")
        return Response(content=f"错误: {str(e)}", status_code=500)


# 注册 SSE 端点
@router.get("/sse")
async def sse_endpoint(request: FastAPIRequest, db: AsyncSession = Depends(get_db)):
    """MCP 服务器的 SSE 端点

    Args:
        request: FastAPI 请求对象
        db: 数据库会话

    Returns:
        Response: SSE 响应
    """
    return await handle_sse(request, db)


# 注册消息处理端点
@router.route("/messages/{path:path}", methods=["POST"])
async def message_handler(request: FastAPIRequest):
    """处理 SSE 传输的消息发送

    Args:
        request: FastAPI 请求对象

    Returns:
        Response: 接受响应

    Raises:
        McpMessageHandlingError: 当处理消息发送时出错时抛出
    """
    try:
        logger.info(f"处理消息发送: {request.url.path}")
        # 获取 SSE 传输
        transport = get_sse_transport()

        # 处理消息发送
        await transport.handle_post_message(
            request.scope, request.receive, request._send
        )
        return Response(status_code=202)  # 202 Accepted
    except Exception as e:
        error_msg = f"处理消息发送时出错: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise McpMessageHandlingError(error_message=str(e))

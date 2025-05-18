import logging
import os
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse
from starlette.staticfiles import StaticFiles

# 获取日志记录器
logger = logging.getLogger(__name__)

# 获取静态文件目录路径
static_dir = Path("static")
index_html_path = static_dir / "index.html"

# 创建路由器
router = APIRouter(tags=["static"])

# 检查静态文件目录是否存在
if not static_dir.exists():
    logger.warning(f"静态文件目录 '{static_dir}' 不存在，将在需要时创建")
    os.makedirs(static_dir, exist_ok=True)

# 检查 index.html 是否存在
if not index_html_path.exists():
    logger.warning(f"静态文件 '{index_html_path}' 不存在")


# 添加回退路由，支持 Vue 路由
@router.get("/{full_path:path}")
async def serve_spa(request: Request, full_path: str):
    """
    提供单页应用 (SPA) 的回退路由，支持 Vue 路由
    
    如果请求的路径是一个文件，则尝试从静态目录提供该文件
    否则返回 index.html 以支持客户端路由
    """
    # 检查请求的路径是否是 API 路由
    if request.url.path.startswith("/api/") or request.url.path.startswith("/sse"):
        return HTMLResponse(
            content="Not Found", status_code=404
        )
    
    # 构建完整的文件路径
    file_path = static_dir / full_path
    
    # 如果文件存在，则直接提供该文件
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    
    # 否则返回 index.html 以支持客户端路由
    if index_html_path.exists():
        return FileResponse(index_html_path)
    else:
        return HTMLResponse(
            content="<html><body><h1>欢迎使用 Easy MCP Server</h1><p>前端文件尚未构建。请运行 <code>npm run build</code> 并将构建结果复制到 static 目录。</p></body></html>",
            status_code=200
        )

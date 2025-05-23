"""
Main application module.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from api.config import get_config, setup_logging
from api.database import create_db_and_tables, get_session
from api.middleware.error_middleware import ServiceErrorMiddleware
from api.middleware.request_id_middleware import RequestIdMiddleware

# Import models to ensure they are registered with SQLModel
from api.models.tb_tool_log import TbToolLog
from api.routers import (
    auth_router,
    user_router,
    tool_router,
    func_router,
    config_router,
    audit_router,
    log_router,
    tool_log_router,
    mcp_router,
    static_router,
    openapi_router,
)
from api.routers.mcp_router import mcp_server_lifespan
from api.utils.init_admin import init_admin_user

# Get configuration
config = get_config()

# Setup logging
setup_logging(config)

# Create logger
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for the application.

    Args:
        app: FastAPI application
    """
    # Startup
    logger.info("Starting up...")

    # Create database tables
    await create_db_and_tables()

    # Initialize admin user
    async with get_session() as db:
        await init_admin_user(db)

    # Initialize MCP server
    async with mcp_server_lifespan():
        logger.info("MCP server initialized")
        yield
        logger.info("MCP server shutdown")

    # Shutdown
    logger.info("Shutting down...")


# Create application
app = FastAPI(
    title=config.title,
    description=config.description,
    version=config.version,
    debug=config.debug,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request ID middleware (should be first to ensure all requests have an ID)
app.add_middleware(RequestIdMiddleware)

# Add error handling middleware
app.add_middleware(ServiceErrorMiddleware)

# Audit middleware has been removed - audit logs are now handled by the audit decorator

# Add routers
app.include_router(auth_router.router, prefix="/api/v1")
app.include_router(user_router.router, prefix="/api/v1")
app.include_router(tool_router.router, prefix="/api/v1")
app.include_router(func_router.router, prefix="/api/v1")
app.include_router(config_router.router, prefix="/api/v1")
app.include_router(audit_router.router, prefix="/api/v1")
app.include_router(log_router.router, prefix="/api/v1")
app.include_router(tool_log_router.router)
app.include_router(openapi_router.router, prefix="/api/v1")

# Add MCP router
app.include_router(mcp_router.router)

# 挂载静态文件目录
static_dir = Path("static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 包含静态文件路由器（支持 Vue 路由）
app.include_router(static_router.router)


@app.get("/api/v1/system")
async def system():
    """System endpoint.

    Returns:
        dict: Welcome message
    """
    return {"message": "Welcome to Easy MCP API"}


@app.get("/")
async def root():
    """Root endpoint.

    Returns:
        RedirectResponse: Redirect to index.html
    """
    return RedirectResponse(url="/static/index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=config.server.host,
        port=config.server.port,
        reload=config.debug,
    )

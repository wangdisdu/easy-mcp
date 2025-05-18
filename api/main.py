"""
Main application module.
"""

import logging
import warnings
from contextlib import asynccontextmanager

# Filter out bcrypt version warning from passlib
warnings.filterwarnings("ignore", message=".*error reading bcrypt version.*")
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import get_config, setup_logging
from api.database import create_db_and_tables, get_session
from api.middleware.audit_middleware import AuditMiddleware
from api.middleware.error_middleware import ServiceErrorMiddleware
from api.routers import (
    auth_router,
    user_router,
    tool_router,
    func_router,
    config_router,
    audit_router,
    mcp_router,
)
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

    yield

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

# Add error handling middleware
app.add_middleware(ServiceErrorMiddleware)

# Add audit middleware
app.add_middleware(AuditMiddleware)

# Add routers
app.include_router(auth_router.router, prefix="/api/v1")
app.include_router(user_router.router, prefix="/api/v1")
app.include_router(tool_router.router, prefix="/api/v1")
app.include_router(func_router.router, prefix="/api/v1")
app.include_router(config_router.router, prefix="/api/v1")
app.include_router(audit_router.router, prefix="/api/v1")
app.include_router(mcp_router.router, prefix="/api/v1")


@app.get("/api/v1/system")
async def root():
    """Root endpoint.

    Returns:
        dict: Welcome message
    """
    return {"message": "Welcome to Easy MCP API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=config.server.host,
        port=config.server.port,
        reload=config.debug,
    )

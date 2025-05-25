"""
Configuration module for the Easy MCP API.
"""

import logging
import logging.config
import os
from typing import List, Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables from .env file
load_dotenv()

# Base directory of the application
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class DatabaseConfig(BaseModel):
    """Database configuration."""

    url: str
    echo: bool = False
    # 连接池配置
    pool_size: int = 5  # 连接池大小
    max_overflow: int = 10  # 最大溢出连接数
    pool_timeout: int = 30  # 连接池超时时间（秒）
    pool_recycle: int = 1800  # 连接回收时间（秒）


class JWTConfig(BaseModel):
    """JWT configuration."""

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 1 day


class AdminUserConfig(BaseModel):
    """Admin user configuration."""

    username: str = "admin"
    password: str = "admin"
    email: str = "admin@example.com"


class AppConfig(BaseModel):
    """Application configuration."""

    debug: bool = False
    title: str = Field(default="Easy MCP")
    version: str = Field(default="0.1.0")
    description: str = Field(default="Dynamic MCP tool registration server")
    database: DatabaseConfig
    jwt: JWTConfig
    cors_origins: List[str] = Field(default=["*"])
    log_level: str = Field(default="INFO")
    log_config_path: Optional[str] = Field(default=None)
    admin_user: AdminUserConfig = Field(default_factory=AdminUserConfig)


def get_config() -> AppConfig:
    """
    Load configuration from environment variables.

    Returns:
        AppConfig: Application configuration
    """
    # Application settings
    app_name = os.getenv("APP_NAME", "Easy MCP API")
    app_version = os.getenv("APP_VERSION", "0.1.0")
    app_description = os.getenv(
        "APP_DESCRIPTION", "Dynamic MCP tool registration server"
    )
    debug = os.getenv("DEBUG", "False").lower() == "true"

    # Database configuration
    db_url = os.getenv("DB_URL", "sqlite+aiosqlite:///./easy_mcp.db")
    db_echo = os.getenv("DB_ECHO", "False").lower() == "true"

    # JWT configuration
    jwt_secret = os.getenv("JWT_SECRET_KEY", "easy_mcp_secret")
    jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expire = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 1 day

    # CORS configuration
    cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")

    # Logging configuration
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_config_path = os.getenv("LOG_CONFIG_PATH", "api/logging.ini")

    # Server configuration
    server_host = os.getenv("HOST", "0.0.0.0")
    server_port = int(os.getenv("PORT", "8000"))

    # Admin user configuration
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin")
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")

    # Tool execution configuration
    tool_timeout = int(os.getenv("TOOL_EXECUTION_TIMEOUT", "30"))
    tool_max_memory = int(os.getenv("TOOL_MAX_MEMORY", "512"))

    return AppConfig(
        debug=debug,
        title=app_name,
        version=app_version,
        description=app_description,
        database=DatabaseConfig(url=db_url, echo=db_echo),
        jwt=JWTConfig(
            secret_key=jwt_secret,
            algorithm=jwt_algorithm,
            access_token_expire_minutes=jwt_expire,
        ),
        cors_origins=cors_origins,
        log_level=log_level,
        log_config_path=log_config_path,
        admin_user=AdminUserConfig(
            username=admin_username, password=admin_password, email=admin_email
        ),
    )


def setup_logging(config: AppConfig) -> None:
    """
    Set up logging configuration.

    Args:
        config: Application configuration
    """
    if config.log_config_path and os.path.exists(config.log_config_path):
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs"
        )
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)

        # Determine file format and load configuration
        file_ext = os.path.splitext(config.log_config_path)[1].lower()
        if file_ext == ".ini":
            # Load INI configuration
            logging.config.fileConfig(
                config.log_config_path, disable_existing_loggers=False
            )
        else:
            # Load YAML configuration
            with open(config.log_config_path, "rt") as f:
                log_config = yaml.safe_load(f.read())
            logging.config.dictConfig(log_config)

        # Log that configuration was loaded
        logger = logging.getLogger(__name__)
        logger.info(f"Loaded logging configuration from {config.log_config_path}")
    else:
        # Basic logging configuration
        logging.basicConfig(
            level=getattr(logging, config.log_level),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

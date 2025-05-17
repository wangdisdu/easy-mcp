"""
Initialize admin user on first startup.
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from api.config import get_config
from api.models.tb_user import TbUser
from api.schemas.user_schema import UserCreate
from api.services.user_service import UserService

# Create logger
logger = logging.getLogger(__name__)

# Get configuration
config = get_config()


async def init_admin_user(db: AsyncSession) -> None:
    """
    Initialize admin user if it doesn't exist.

    Args:
        db: Database session
    """
    # Check if admin user exists
    result = await db.execute(
        select(TbUser).where(TbUser.username == config.admin_user.username)
    )
    admin_user = result.scalars().first()

    if admin_user:
        logger.info(f"Admin user '{config.admin_user.username}' already exists")
        return

    # Create admin user
    logger.info(f"Creating admin user '{config.admin_user.username}'")

    service = UserService(db)
    user_data = UserCreate(
        username=config.admin_user.username,
        password=config.admin_user.password,
        email=config.admin_user.email,
    )

    await service.create_user(user_data, "system")

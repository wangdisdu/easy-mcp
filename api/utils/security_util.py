"""
Security utility functions.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from api.config import get_config
from api.database import get_db
from api.errors.user_error import InvalidCredentialsError
from api.models.tb_user import TbUser

# Get configuration
config = get_config()
SECRET_KEY = config.jwt.secret_key
ALGORITHM = config.jwt.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = config.jwt.access_token_expire_minutes
ADMIN_USERNAME = config.admin_user.username

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated=["auto"])

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Get logger
logger = logging.getLogger(__name__)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hashed password.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password

    Returns:
        bool: True if password is correct, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash password.

    Args:
        password: Plain text password

    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token.

    Args:
        data: Data to encode in token
        expires_delta: Token expiration time

    Returns:
        str: JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


async def authenticate_user(db: AsyncSession, username: str, password: str) -> TbUser:
    """
    Authenticate user.

    Args:
        db: Database session
        username: Username
        password: Password

    Returns:
        TbUser: User object

    Raises:
        InvalidCredentialsError: If credentials are invalid
    """
    result = await db.execute(select(TbUser).where(TbUser.username == username))
    user = result.scalars().first()

    if not user:
        logger.warning(f"User '{username}' not found")
        raise InvalidCredentialsError()

    if not verify_password(password, user.password):
        logger.warning(f"Invalid password for user '{username}'")
        raise InvalidCredentialsError()

    return user


async def check_is_admin(user: TbUser) -> None:
    """
    Check if user is admin.

    Args:
        user: User object

    Raises:
        HTTPException: If user is not admin
    """
    # 使用配置中的管理员用户名判断
    if user.username != ADMIN_USERNAME:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this resource",
        )


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> TbUser:
    """
    Get current user from token.

    Args:
        token: JWT token
        db: Database session

    Returns:
        TbUser: User object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")

        if username is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    result = await db.execute(select(TbUser).where(TbUser.username == username))
    user = result.scalars().first()

    if user is None:
        raise credentials_exception

    return user

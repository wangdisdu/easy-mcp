"""
Authentication router.
"""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import get_config
from api.database import get_db
from api.errors.user_error import InvalidCredentialsError
from api.schemas.common_schema import Response
from api.schemas.user_schema import LoginRequest, TokenResponse
from api.utils.security_util import authenticate_user, create_access_token

# Get JWT configuration
config = get_config()
ACCESS_TOKEN_EXPIRE_MINUTES = config.jwt.access_token_expire_minutes

# Create router
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Response[TokenResponse])
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Login endpoint.

    Args:
        login_data: Login data
        db: Database session

    Returns:
        Response[TokenResponse]: JWT token

    Raises:
        HTTPException: If credentials are invalid
    """
    try:
        user = await authenticate_user(db, login_data.username, login_data.password)

        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )

        return Response(data=TokenResponse(token=access_token))

    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

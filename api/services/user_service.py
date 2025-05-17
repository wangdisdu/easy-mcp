"""
User service.
"""

from typing import Optional, List, Tuple

from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from api.errors.user_error import UserNotFoundError, UserAlreadyExistsError
from api.models.tb_user import TbUser
from api.schemas.user_schema import UserCreate, UserUpdate
from api.utils.audit_util import audit
from api.utils.security_util import get_password_hash
from api.utils.time_util import get_current_unix_ms


class UserService:
    """
    User service.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize user service.

        Args:
            db: Database session
        """
        self.db = db

    async def get_user_by_id(self, user_id: int) -> Optional[TbUser]:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            TbUser: User object or None if not found
        """
        result = await self.db.execute(select(TbUser).where(TbUser.id == user_id))
        return result.scalars().first()

    async def get_user_by_username(self, username: str) -> Optional[TbUser]:
        """
        Get user by username.

        Args:
            username: Username

        Returns:
            TbUser: User object or None if not found
        """
        result = await self.db.execute(
            select(TbUser).where(TbUser.username == username)
        )
        return result.scalars().first()

    async def query_users(
        self, page: int = 1, size: int = 20, search: Optional[str] = None
    ) -> Tuple[List[TbUser], int]:
        """
        Query users with pagination.

        Args:
            page: Page number (1-based)
            size: Page size
            search: Search term for username or email (optional)

        Returns:
            Tuple[List[TbUser], int]: List of users and total count
        """
        query = select(TbUser)

        # Apply filters
        if search:
            query = query.where(
                or_(
                    TbUser.username.ilike(f"%{search}%"),
                    TbUser.email.ilike(f"%{search}%"),
                )
            )

        # Count total
        count_result = await self.db.execute(select(TbUser.id).where(query.whereclause))
        total = len(count_result.scalars().all())

        # Apply pagination
        query = query.offset((page - 1) * size).limit(size)

        # Execute query
        result = await self.db.execute(query)
        users = result.scalars().all()

        return list(users), total

    @audit(operation_type="create", object_type="user")
    async def create_user(
        self, user_data: UserCreate, current_user: Optional[str] = None
    ) -> TbUser:
        """
        Create a new user.

        Args:
            user_data: User data
            current_user: Current username

        Returns:
            TbUser: Created user

        Raises:
            UserAlreadyExistsError: If user already exists
        """
        # Check if user already exists
        existing_user = await self.get_user_by_username(user_data.username)
        if existing_user:
            raise UserAlreadyExistsError(username=user_data.username)

        # Create user
        current_time = get_current_unix_ms()
        user = TbUser(
            username=user_data.username,
            password=get_password_hash(user_data.password),
            email=user_data.email,
            created_at=current_time,
            updated_at=current_time,
            created_by=current_user,
            updated_by=current_user,
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    @audit(operation_type="update", object_type="user")
    async def update_user(
        self, user_id: int, user_data: UserUpdate, current_user: Optional[str] = None
    ) -> Optional[TbUser]:
        """
        Update user.

        Args:
            user_id: User ID
            user_data: User data
            current_user: Current username

        Returns:
            TbUser: Updated user or None if not found

        Raises:
            UserNotFoundError: If user not found
        """
        # Get user
        user = await self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)

        # Update user
        if user_data.email is not None:
            user.email = user_data.email

        if user_data.password is not None:
            user.password = get_password_hash(user_data.password)

        user.updated_at = get_current_unix_ms()
        user.updated_by = current_user

        await self.db.commit()
        await self.db.refresh(user)

        return user

    @audit(operation_type="delete", object_type="user")
    async def delete_user(
        self, user_id: int, current_user: Optional[str] = None
    ) -> Optional[TbUser]:
        """
        Delete user.

        Args:
            user_id: User ID
            current_user: Current username

        Returns:
            TbUser: Deleted user or None if not found

        Raises:
            UserNotFoundError: If user not found
        """
        # Get user
        user = await self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)

        # Delete user
        await self.db.delete(user)
        await self.db.commit()

        return user

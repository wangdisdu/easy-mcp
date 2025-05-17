"""
Function service.
"""

from typing import Optional, List, Tuple

from sqlalchemy import or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from api.errors.func_error import (
    FuncNotFoundError,
    FuncAlreadyExistsError,
    FuncInUseError,
    FuncVersionNotFoundError,
    CircularDependencyError,
)
from api.models.tb_func import TbFunc, TbFuncDeploy, TbFuncDepends
from api.models.tb_tool import TbTool, TbToolFunc
from api.schemas.func_schema import FuncCreate, FuncUpdate
from api.schemas.usage_schema import FuncUsageResponse
from api.utils.audit_util import audit
from api.utils.time_util import get_current_unix_ms


class FuncService:
    """
    Function service.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize function service.

        Args:
            db: Database session
        """
        self.db = db

    async def get_func_by_id(self, func_id: int) -> Optional[TbFunc]:
        """
        Get function by ID.

        Args:
            func_id: Function ID

        Returns:
            TbFunc: Function object or None if not found
        """
        result = await self.db.execute(select(TbFunc).where(TbFunc.id == func_id))
        return result.scalars().first()

    async def get_func_by_name(self, name: str) -> Optional[TbFunc]:
        """
        Get function by name.

        Args:
            name: Function name

        Returns:
            TbFunc: Function object or None if not found
        """
        result = await self.db.execute(select(TbFunc).where(TbFunc.name == name))
        return result.scalars().first()

    async def query_funcs(
        self, page: int = 1, size: int = 20, search: Optional[str] = None
    ) -> Tuple[List[TbFunc], int]:
        """
        Query functions with pagination.

        Args:
            page: Page number (1-based)
            size: Page size
            search: Search term for name or description

        Returns:
            Tuple[List[TbFunc], int]: List of functions and total count
        """
        query = select(TbFunc)

        # Apply filters
        if search:
            query = query.where(
                or_(
                    TbFunc.name.ilike(f"%{search}%"),
                    TbFunc.description.ilike(f"%{search}%"),
                )
            )

        # Count total
        count_result = await self.db.execute(
            select(TbFunc.id).where(query.whereclause)
            if query.whereclause
            else select(TbFunc.id)
        )
        total = len(count_result.scalars().all())

        # Apply pagination and ordering
        query = query.order_by(desc(TbFunc.id)).offset((page - 1) * size).limit(size)

        # Execute query
        result = await self.db.execute(query)
        funcs = result.scalars().all()

        return list(funcs), total

    async def check_circular_dependency(
        self, func_id: int, depend_ids: List[int], path: Optional[List[int]] = None
    ) -> None:
        """
        Check for circular dependencies.

        Args:
            func_id: Function ID
            depend_ids: Dependency function IDs
            path: Current dependency path

        Raises:
            CircularDependencyError: If circular dependency is detected
        """
        if path is None:
            path = []

        # Check if func_id is in depend_ids
        if func_id in depend_ids:
            raise CircularDependencyError(func_id=func_id, dependency_path=path)

        # Check each dependency
        for depend_id in depend_ids:
            if depend_id in path:
                raise CircularDependencyError(
                    func_id=func_id, dependency_path=path + [depend_id]
                )

            # Get dependencies of this dependency
            result = await self.db.execute(
                select(TbFuncDepends.depends_on_func_id).where(
                    TbFuncDepends.func_id == depend_id
                )
            )
            nested_depend_ids = [row[0] for row in result]

            # Recursively check
            if nested_depend_ids:
                await self.check_circular_dependency(
                    func_id, nested_depend_ids, path + [depend_id]
                )

    @audit(operation_type="create", object_type="func")
    async def create_func(
        self, func_data: FuncCreate, current_user: Optional[str] = None
    ) -> TbFunc:
        """
        Create a new function.

        Args:
            func_data: Function data
            current_user: Current username

        Returns:
            TbFunc: Created function

        Raises:
            FuncAlreadyExistsError: If function already exists
            CircularDependencyError: If circular dependency is detected
        """
        # Check if function already exists
        existing_func = await self.get_func_by_name(func_data.name)
        if existing_func:
            raise FuncAlreadyExistsError(name=func_data.name)

        # Create function
        current_time = get_current_unix_ms()
        func = TbFunc(
            name=func_data.name,
            description=func_data.description,
            code=func_data.code,
            created_at=current_time,
            updated_at=current_time,
            created_by=current_user,
            updated_by=current_user,
        )

        self.db.add(func)
        await self.db.commit()
        await self.db.refresh(func)

        # Add dependencies
        if func_data.depend_ids:
            # Check for circular dependencies
            await self.check_circular_dependency(func.id, func_data.depend_ids)

            for depend_id in func_data.depend_ids:
                depend = TbFuncDepends(
                    func_id=func.id,
                    depends_on_func_id=depend_id,
                    created_at=current_time,
                    updated_at=current_time,
                    created_by=current_user,
                    updated_by=current_user,
                )
                self.db.add(depend)

        await self.db.commit()

        return func

    @audit(operation_type="update", object_type="func")
    async def update_func(
        self, func_id: int, func_data: FuncUpdate, current_user: Optional[str] = None
    ) -> Optional[TbFunc]:
        """
        Update function.

        Args:
            func_id: Function ID
            func_data: Function data
            current_user: Current username

        Returns:
            TbFunc: Updated function or None if not found

        Raises:
            FuncNotFoundError: If function not found
            FuncAlreadyExistsError: If function name already exists
            CircularDependencyError: If circular dependency is detected
        """
        # Get function
        func = await self.get_func_by_id(func_id)
        if not func:
            raise FuncNotFoundError(func_id=func_id)

        # Check if name already exists
        if func_data.name != func.name:
            existing_func = await self.get_func_by_name(func_data.name)
            if existing_func:
                raise FuncAlreadyExistsError(name=func_data.name)

        # Update function
        func.name = func_data.name
        func.description = func_data.description
        func.code = func_data.code
        func.updated_at = get_current_unix_ms()
        func.updated_by = current_user

        # Update dependencies
        if func_data.depend_ids is not None:
            # Check for circular dependencies
            await self.check_circular_dependency(func_id, func_data.depend_ids)

            # Delete existing dependencies
            await self.db.execute(
                TbFuncDepends.__table__.delete().where(TbFuncDepends.func_id == func_id)
            )

            # Add new dependencies
            current_time = get_current_unix_ms()
            for depend_id in func_data.depend_ids:
                depend = TbFuncDepends(
                    func_id=func.id,
                    depends_on_func_id=depend_id,
                    created_at=current_time,
                    updated_at=current_time,
                    created_by=current_user,
                    updated_by=current_user,
                )
                self.db.add(depend)

        await self.db.commit()
        await self.db.refresh(func)

        return func

    @audit(operation_type="deploy", object_type="func")
    async def deploy_func(
        self,
        func_id: int,
        description: Optional[str] = None,
        current_user: Optional[str] = None,
    ) -> TbFuncDeploy:
        """
        Deploy function.

        Args:
            func_id: Function ID
            description: Deployment description
            current_user: Current username

        Returns:
            TbFuncDeploy: Function deployment

        Raises:
            FuncNotFoundError: If function not found
        """
        # Get function
        func = await self.get_func_by_id(func_id)
        if not func:
            raise FuncNotFoundError(func_id=func_id)

        # Get next version
        version = 1
        if func.current_version:
            version = func.current_version + 1

        # Create deployment
        current_time = get_current_unix_ms()
        deploy = TbFuncDeploy(
            func_id=func.id,
            version=version,
            code=func.code,
            description=description,
            created_at=current_time,
            updated_at=current_time,
            created_by=current_user,
            updated_by=current_user,
        )

        self.db.add(deploy)

        # Update function version
        func.current_version = version

        await self.db.commit()
        await self.db.refresh(deploy)

        return deploy

    async def get_func_deploy_history(
        self, func_id: int, page: int = 1, size: int = 20
    ) -> Tuple[List[TbFuncDeploy], int]:
        """
        Get function deployment history.

        Args:
            func_id: Function ID
            page: Page number (1-based)
            size: Page size

        Returns:
            Tuple[List[TbFuncDeploy], int]: List of deployments and total count

        Raises:
            FuncNotFoundError: If function not found
        """
        # Check if function exists
        func = await self.get_func_by_id(func_id)
        if not func:
            raise FuncNotFoundError(func_id=func_id)

        # Query deployments
        query = select(TbFuncDeploy).where(TbFuncDeploy.func_id == func_id)

        # Count total
        count_result = await self.db.execute(
            select(TbFuncDeploy.id).where(TbFuncDeploy.func_id == func_id)
        )
        total = len(count_result.scalars().all())

        # Apply pagination and ordering
        query = (
            query.order_by(desc(TbFuncDeploy.version))
            .offset((page - 1) * size)
            .limit(size)
        )

        # Execute query
        result = await self.db.execute(query)
        deploys = result.scalars().all()

        return list(deploys), total

    @audit(operation_type="rollback", object_type="func")
    async def rollback_func(
        self, func_id: int, version: int, current_user: Optional[str] = None
    ) -> TbFunc:
        """
        Rollback function to a specific version.

        Args:
            func_id: Function ID
            version: Version to rollback to
            current_user: Current username

        Returns:
            TbFunc: Updated function

        Raises:
            FuncNotFoundError: If function not found
            FuncVersionNotFoundError: If version not found
        """
        # Get function
        func = await self.get_func_by_id(func_id)
        if not func:
            raise FuncNotFoundError(func_id=func_id)

        # Get deployment
        result = await self.db.execute(
            select(TbFuncDeploy).where(
                TbFuncDeploy.func_id == func_id, TbFuncDeploy.version == version
            )
        )
        deploy = result.scalars().first()

        if not deploy:
            raise FuncVersionNotFoundError(func_id=func_id, version=version)

        # Update function
        func.code = deploy.code
        func.updated_at = get_current_unix_ms()
        func.updated_by = current_user

        await self.db.commit()
        await self.db.refresh(func)

        return func

    async def check_func_in_use(
        self, func_id: int
    ) -> Tuple[bool, List[dict], List[dict]]:
        """
        Check if function is in use.

        Args:
            func_id: Function ID

        Returns:
            Tuple[bool, List[dict], List[dict]]: Is in use, tools using it, functions using it
        """
        # Check if used by tools
        result = await self.db.execute(
            select(TbToolFunc).where(TbToolFunc.func_id == func_id)
        )
        tool_funcs = result.scalars().all()

        # Check if used by other functions
        result = await self.db.execute(
            select(TbFuncDepends).where(TbFuncDepends.depends_on_func_id == func_id)
        )
        func_depends = result.scalars().all()

        # Get tool details
        tools_using = []
        for tool_func in tool_funcs:
            result = await self.db.execute(
                select(TbFunc).where(TbFunc.id == tool_func.tool_id)
            )
            tool = result.scalars().first()
            if tool:
                tools_using.append({"id": tool.id, "name": tool.name})

        # Get function details
        funcs_using = []
        for func_depend in func_depends:
            result = await self.db.execute(
                select(TbFunc).where(TbFunc.id == func_depend.func_id)
            )
            func = result.scalars().first()
            if func:
                funcs_using.append({"id": func.id, "name": func.name})

        is_in_use = len(tools_using) > 0 or len(funcs_using) > 0

        return is_in_use, tools_using, funcs_using

    @audit(operation_type="delete", object_type="func")
    async def delete_func(
        self, func_id: int, current_user: Optional[str] = None
    ) -> Optional[TbFunc]:
        """
        Delete function.

        Args:
            func_id: Function ID
            current_user: Current username

        Returns:
            TbFunc: Deleted function or None if not found

        Raises:
            FuncNotFoundError: If function not found
            FuncInUseError: If function is in use
        """
        # Get function
        func = await self.get_func_by_id(func_id)
        if not func:
            raise FuncNotFoundError(func_id=func_id)

        # Check if function is in use
        is_in_use, tools_using, funcs_using = await self.check_func_in_use(func_id)
        if is_in_use:
            raise FuncInUseError(
                func_id=func_id, used_by_tools=tools_using, used_by_funcs=funcs_using
            )

        # Delete function
        await self.db.delete(func)
        await self.db.commit()

        return func

    async def get_func_usage(self, func_id: int) -> FuncUsageResponse:
        """
        Get usage information for a function.

        Args:
            func_id: Function ID

        Returns:
            FuncUsageResponse: Usage information for the function

        Raises:
            FuncNotFoundError: If function not found
        """
        # Check if function exists
        func = await self.get_func_by_id(func_id)
        if not func:
            raise FuncNotFoundError(func_id=func_id)

        # Get tools using this function
        result = await self.db.execute(
            select(TbTool)
            .join(TbToolFunc, TbToolFunc.tool_id == TbTool.id)
            .where(TbToolFunc.func_id == func_id)
        )
        tools = result.scalars().all()

        # Get functions that depend on this function
        result = await self.db.execute(
            select(TbFunc)
            .join(TbFuncDepends, TbFuncDepends.func_id == TbFunc.id)
            .where(TbFuncDepends.depends_on_func_id == func_id)
        )
        funcs = result.scalars().all()

        # Create response
        from api.schemas.tool_schema import ToolResponse
        from api.schemas.func_schema import FuncResponse

        tool_responses = [ToolResponse.model_validate(tool) for tool in tools]
        func_responses = [FuncResponse.model_validate(f) for f in funcs]

        return FuncUsageResponse(tools=tool_responses, funcs=func_responses)

    async def get_func_dependencies(self, func_id: int) -> List[TbFunc]:
        """
        Get dependencies of a function.

        Args:
            func_id: Function ID

        Returns:
            List[TbFunc]: List of functions this function depends on

        Raises:
            FuncNotFoundError: If function not found
        """
        # Check if function exists
        func = await self.get_func_by_id(func_id)
        if not func:
            raise FuncNotFoundError(func_id=func_id)

        # Get functions that this function depends on
        result = await self.db.execute(
            select(TbFunc)
            .join(TbFuncDepends, TbFuncDepends.depends_on_func_id == TbFunc.id)
            .where(TbFuncDepends.func_id == func_id)
        )
        dependencies = result.scalars().all()

        return dependencies

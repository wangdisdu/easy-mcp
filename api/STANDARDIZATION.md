# FastAPI 后端代码风格标准

本文档定义了 Easy MCP 项目 API 后端代码的标准化规范，旨在确保代码的一致性、可维护性和可读性。所有贡献者应遵循这些规范，以保持代码库的质量和一致性。

## 目录

1. [项目结构](#项目结构)
2. [命名约定](#命名约定)
3. [路由器（Router）规范](#路由器规范)
4. [服务（Service）规范](#服务规范)
5. [模型和架构（Model & Schema）规范](#模型和架构规范)
6. [错误处理规范](#错误处理规范)
7. [依赖注入规范](#依赖注入规范)
8. [日志记录规范](#日志记录规范)
9. [审计日志规范](#审计日志规范)
10. [代码格式化](#代码格式化)
11. [注释规范](#注释规范)

## 项目结构

```
api/
├── config.py                # 应用配置
├── database.py              # 数据库连接和会话管理
├── main.py                  # 应用入口点
├── requirements.txt         # 依赖项
├── errors/                  # 错误类定义
│   ├── base_error.py        # 基础错误类
│   ├── user_error.py        # 用户相关错误
│   └── ...
├── middleware/              # 中间件
│   ├── audit_middleware.py  # 审计中间件
│   └── ...
├── models/                  # 数据库模型
│   ├── tb_user.py           # 用户表模型
│   └── ...
├── routers/                 # API 路由
│   ├── user_router.py       # 用户相关路由
│   └── ...
├── schemas/                 # Pydantic 模型/架构
│   ├── user_schema.py       # 用户相关架构
│   └── ...
├── services/                # 业务逻辑服务
│   ├── user_service.py      # 用户相关服务
│   └── ...
└── utils/                   # 工具函数
    ├── security_util.py     # 安全相关工具
    └── ...
```

## 命名约定

### 文件命名

- 路由器文件：`*_router.py`（例如：`user_router.py`）
- 服务文件：`*_service.py`（例如：`user_service.py`）
- 工具文件：`*_util.py`（例如：`security_util.py`）
- 模型文件：`tb_*.py`（例如：`tb_user.py`）
- 架构文件：`*_schema.py`（例如：`user_schema.py`）
- 错误文件：`*_error.py`（例如：`user_error.py`）

### API 端点命名

- 使用单数形式命名资源（例如：`/api/v1/user` 而非 `/api/v1/users`）

### 变量和函数命名

- 使用 snake_case 命名变量和函数（例如：`user_service`，`get_current_user`）
- 使用 PascalCase 命名类（例如：`UserService`，`TbUser`）
- 使用 UPPER_CASE 命名常量（例如：`SECRET_KEY`，`ACCESS_TOKEN_EXPIRE_MINUTES`）

## 路由器规范

### 路由器规范要点

1. **路由器职责**：
   - 路由器只负责请求的接收和响应的返回
   - 不应包含业务逻辑，业务逻辑应放在服务层
   - 不应直接抛出 HTTPException，应使用对应的 Error 类

2. **端点命名**：
   - 使用 RESTful 风格命名端点
   - 使用 HTTP 方法表示操作（GET、POST、PUT、DELETE）
   - 使用单数形式命名资源

3. **响应模型**：
   - 始终使用 `response_model` 参数指定响应模型
   - 对于分页查询，使用 `PaginatedResponse` 作为响应模型

4. **依赖注入**：
   - 使用 `Depends` 注入数据库会话和当前用户
   - 对于需要身份验证的端点，始终注入 `current_user`

## 服务规范

### 服务规范要点

1. **服务职责**：
   - 服务负责实现业务逻辑
   - 服务方法应该是原子的，完成单一职责
   - 服务应该处理所有业务规则验证

2. **方法命名约定**：
   - `get_*`：获取单个资源，返回 Optional
   - `query_*`：分页查询资源，返回 Tuple[List, int]（结果列表和总数）
   - `create_*`：创建资源，如果资源已存在则抛出 *AlreadyExistsError
   - `update_*`：更新资源，返回 Optional（找不到资源时返回 None）
   - `delete_*`：删除资源，返回 Optional（找不到资源时返回 None），如果正被引用返回*InUseError

3. **错误处理**：
   - 使用自定义错误类而非直接抛出 HTTPException
   - 在适当的地方记录警告和错误日志

4. **审计日志**：
   - 对于修改操作（创建、更新、删除），使用 `@audit` 装饰器记录审计日志
   - 审计日志应包含操作类型、对象类型、操作者和请求信息

5. **时间处理**：
   - 使用 `get_current_unix_ms()` 获取当前时间戳

6. **查询方法**：
   - 查询方法应支持分页
   - 默认按 ID 降序排序
   - 支持搜索过滤

## 模型和架构规范

### 数据库模型

```python
from sqlmodel import Field, SQLModel
from typing import Optional

class TbUser(SQLModel, table=True):
    __tablename__ = "tb_user"

    id: int = Field(primary_key=True)
    account: str = Field(index=True)
    password: str
    create_time: Optional[int] = Field(default=None)  # UnixMs 时间戳
    update_time: Optional[int] = Field(default=None)  # UnixMs 时间戳
    create_user: Optional[str] = Field(default=None)
    update_user: Optional[str] = Field(default=None)
```

### Pydantic 架构

### 模型和架构规范要点

1. **数据库模型**：
   - 表名使用 `tb_` 前缀
   - ID 字段应为主键且不能为空
   - 时间戳字段使用 UnixMs 整数格式

2. **Pydantic 架构**：
   - 使用继承创建基础架构、创建架构、更新架构和响应架构
   - 使用 `Field` 添加字段描述和验证规则
   - 响应架构应包含 `from_attributes = True` 配置

3. **枚举类型**：
   - 使用 `Enum` 定义枚举类型
   - 枚举类应放在相应的架构文件中

4. **分页架构**：
   - 使用 `PaginationParams` 作为分页查询参数
   - 使用 `PaginatedResponse` 作为分页响应模型

## 错误处理规范

### 基础错误类

```python
class ServiceError(ValueError):
    """应用中所有服务级异常的基类。

    该异常应用于所有需要向客户端传达特定错误消息和原因的业务逻辑错误。

    属性:
        code: 标识错误类型的字符串代码
        reason: 错误的人类可读原因
        description: 错误的更详细描述
        details: 关于错误的附加详细信息（可选）
    """

    def __init__(
        self,
        reason: str,
        description: Optional[str] = None,
        code: str = "SERVICE_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.code = code
        self.reason = reason
        self.description = description or reason
        self.details = details or {}
        super().__init__(self.description)
```

### 特定错误类

```python
class UserNotFoundError(ServiceError):
    """当用户未找到时抛出"""

    def __init__(self, user_id=None, account=None):
        details = {}
        if user_id is not None:
            details["user_id"] = user_id
        if account is not None:
            details["account"] = account

        super().__init__(
            reason="未找到用户",
            description=f"未找到用户: {account or user_id}",
            code="USER_NOT_FOUND",
            details=details,
        )
```

### 错误处理规范要点

1. **错误类层次结构**：
   - 所有业务错误应继承自 `ServiceError`
   - 每种资源类型应有自己的错误文件和错误类

2. **错误信息**：
   - 错误消息应使用中文
   - 错误代码应使用大写英文和下划线
   - 错误描述应提供更详细的信息
   - 错误详情应包含相关的标识符和值

3. **错误处理中间件**：
   - 使用 `ServiceErrorMiddleware` 处理所有 `ServiceError` 异常
   - 返回标准化的错误响应，状态码为 400

4. **常见错误类型**：
   - `*NotFoundError`：资源未找到
   - `*AlreadyExistsError`：资源已存在
   - `*ValidationError`：验证失败
   - `*InUseError`：资源正在使用中

## 依赖注入规范

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models.tb_user import TbUser
from api.utils.security_util import get_current_user

async def get_users(
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user)
):
    # 使用注入的依赖项
```

### 依赖注入规范要点

1. **数据库会话**：
   - 使用 `Depends(get_db)` 注入数据库会话
   - 不要手动创建数据库会话

2. **当前用户**：
   - 使用 `Depends(get_current_user)` 注入当前用户
   - 对于需要身份验证的端点，始终注入当前用户

3. **服务实例**：
   - 在路由函数中创建服务实例，而不是作为依赖项注入
   - 将数据库会话传递给服务构造函数

## 日志记录规范

```python
import logging

# 获取日志记录器
logger = logging.getLogger(__name__)

# 使用日志记录器
logger.info("这是一条信息日志")
logger.warning("这是一条警告日志")
logger.error("这是一条错误日志")
logger.exception("这是一条异常日志，包含堆栈跟踪")
```

### 日志记录规范要点

1. **日志级别**：
   - `info`：正常操作信息
   - `warning`：警告信息，不影响操作但需要注意
   - `error`：错误信息，操作失败
   - `exception`：异常信息，包含堆栈跟踪

2. **日志内容**：
   - 日志消息应清晰描述发生的事件
   - 包含相关的标识符和值
   - 对于错误和异常，包含错误原因

3. **日志配置**：
   - 使用 `logging.ini` 配置日志
   - 如果配置文件不存在，使用基本配置

## 审计日志规范

```python
from api.utils.audit_util import audit

@audit(operation_type="create", object_type="user")
async def create_user(
    self,
    user_data: UserCreate,
    current_user: Optional[str] = None,
    request: Optional[Request] = None,
) -> TbUser:
    # 创建用户逻辑...
```

### 审计日志规范要点

1. **审计装饰器**：
   - 使用 `@audit` 装饰器记录审计日志
   - 指定操作类型和对象类型

2. **审计信息**：
   - 操作类型：create、update、delete、publish、rollback 等
   - 对象类型：user、tool、function、config 等
   - 操作者：当前用户
   - 操作时间：当前时间戳
   - 操作 IP：请求 IP
   - 操作结果：成功或失败

3. **审计中间件**：
   - 使用 `AuditMiddleware` 记录 HTTP 请求的审计日志

## 代码格式化

使用 `ruff format` 格式化 API 代码，确保代码风格一致。

### 代码格式化规范要点

1. **导入顺序**：
   - 标准库导入
   - 第三方库导入
   - 本地应用导入

2. **空行**：
   - 顶级函数和类之间使用两个空行
   - 类中的方法之间使用一个空行
   - 相关的导入组之间使用一个空行

3. **行长度**：
   - 遵循 PEP 8 的行长度限制（通常为 88 或 79 个字符）

## 注释规范

```python
def get_user_by_id(self, user_id: int) -> Optional[TbUser]:
    """根据 ID 获取用户。

    Args:
        user_id: 用户 ID

    Returns:
        找到的用户对象，如果未找到则返回 None
    """
    result = await self.db.execute(select(TbUser).where(TbUser.id == user_id))
    return result.scalars().first()
```

### 注释规范要点

1. **文档字符串**：
   - 使用三重引号 `"""` 编写文档字符串
   - 包含简短描述、参数说明和返回值说明
   - 对于复杂函数，包含示例和异常说明

2. **行内注释**：
   - 使用 `#` 编写行内注释
   - 注释应解释代码的意图，而不是重复代码的内容
   - 注释应与代码保持同步

3. **TODO 注释**：
   - 使用 `# TODO: ` 标记待办事项
   - 包含具体的任务描述和（可选的）负责人

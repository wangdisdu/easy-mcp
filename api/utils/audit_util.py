"""
Audit utility functions.
"""

import functools
import inspect
import json
import logging
from datetime import datetime
from typing import Optional, Any, Callable, TypeVar, Awaitable, cast, Dict, List, Union

from fastapi import Request
from api.models.tb_audit import TbAudit
from api.utils.time_util import get_current_unix_ms

# Create logger
logger = logging.getLogger(__name__)

# Type variables for function signatures
F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


def _json_serializable(obj: Any) -> Any:
    """将对象转换为可 JSON 序列化的形式

    Args:
        obj: 要转换的对象

    Returns:
        可序列化的对象
    """
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: _json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_json_serializable(item) for item in obj]
    elif hasattr(obj, "model_dump"):  # Pydantic v2
        return _json_serializable(obj.model_dump())
    elif hasattr(obj, "dict"):  # Pydantic v1
        return _json_serializable(obj.dict())
    elif hasattr(obj, "__dict__"):
        return _json_serializable(obj.__dict__)
    else:
        return str(obj)


def _extract_resource_info(obj: Any) -> tuple[Optional[int], Optional[str]]:
    """从对象中提取资源ID和名称

    Args:
        obj: 要提取信息的对象

    Returns:
        tuple: (resource_id, resource_name)
    """
    resource_id = None
    resource_name = None

    # 从对象中获取ID
    if hasattr(obj, "id"):
        resource_id = obj.id

    # 从对象中获取名称
    if hasattr(obj, "name"):
        resource_name = obj.name
    elif hasattr(obj, "username"):
        resource_name = obj.username

    return resource_id, resource_name


async def _create_audit_log(
    db_session: Any,
    username: str,
    action: str,
    resource_type: str,
    resource_id: Optional[int],
    resource_name: Optional[str],
    details: Dict[str, Any],
    ip_address: Optional[str],
) -> None:
    """创建并保存审计日志

    Args:
        db_session: 数据库会话
        username: 用户名
        action: 操作类型
        resource_type: 资源类型
        resource_id: 资源ID
        resource_name: 资源名称
        details: 详细信息
        ip_address: IP地址
    """
    audit_log = TbAudit(
        username=username,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        resource_name=resource_name,
        details=json.dumps(details, default=str),
        ip_address=ip_address,
        created_at=get_current_unix_ms(),
    )

    try:
        db_session.add(audit_log)
        await db_session.commit()
    except Exception as e:
        logger.error(f"Error creating audit log: {str(e)}")
        try:
            await db_session.rollback()
        except Exception as rollback_error:
            logger.error(f"Error rolling back audit transaction: {str(rollback_error)}")


def audit(operation_type: str, object_type: str) -> Callable[[F], F]:
    """
    Decorator to audit operations.

    Args:
        operation_type: Type of operation (create, update, delete, etc.)
        object_type: Type of object (user, tool, function, etc.)

    Returns:
        Callable: Decorated function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 获取函数签名和参数
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # 提取参数
            current_user: Optional[str] = None
            request: Optional[Request] = None
            resource_id: Optional[int] = None
            resource_name: Optional[str] = None

            # 从参数中查找相关信息
            # 存储所有 *_data 参数用于详细信息
            data_params = {}

            for param_name, param_value in bound_args.arguments.items():
                if param_name == "current_user" and param_value is not None:
                    if hasattr(param_value, "username"):
                        current_user = param_value.username
                    else:
                        current_user = str(param_value)
                elif param_name == "request" and isinstance(param_value, Request):
                    request = param_value
                elif param_name.endswith("_id") and isinstance(param_value, int):
                    resource_id = param_value
                elif param_name in ["name", "username"] and isinstance(
                    param_value, str
                ):
                    resource_name = param_value
                elif param_name.endswith("_data") and param_value is not None:
                    # 从数据对象中提取信息
                    if hasattr(param_value, "name") and param_value.name:
                        resource_name = param_value.name
                    elif hasattr(param_value, "username") and param_value.username:
                        resource_name = param_value.username

                    # 将 *_data 参数保存到详细信息中
                    try:
                        # 使用辅助函数将对象转换为可序列化的形式
                        data_params[param_name] = _json_serializable(param_value)
                    except Exception as e:
                        logger.debug(
                            f"Could not convert {param_name} to serializable format: {str(e)}"
                        )

            audit_db = None

            try:
                # 获取数据库连接
                from api.database import get_db

                try:
                    db_gen = get_db()
                    audit_db = await anext(db_gen)
                except Exception as db_error:
                    logger.error(
                        f"Error creating database connection for audit: {str(db_error)}"
                    )

                # 执行原始函数
                result = await func(*args, **kwargs)

                # 如果有数据库连接，创建审计日志
                if audit_db is not None:
                    # 从结果中补充资源信息
                    if result is not None:
                        if resource_id is None or resource_name is None:
                            if isinstance(result, list) and result:
                                # 如果结果是列表，使用第一个元素
                                res_id, res_name = _extract_resource_info(result[0])
                            else:
                                # 否则直接使用结果对象
                                res_id, res_name = _extract_resource_info(result)

                            if resource_id is None:
                                resource_id = res_id
                            if resource_name is None:
                                resource_name = res_name

                    # 如果有资源ID但没有资源名称，使用默认格式
                    if resource_id is not None and resource_name is None:
                        resource_name = f"{object_type}_{resource_id}"

                    # 准备详细信息
                    details = data_params.copy()  # 使用保存的 *_data 参数作为详细信息

                    # 如果没有 *_data 参数或是创建操作，添加结果信息
                    if not details or operation_type == "create" and result is not None:
                        if hasattr(result, "id"):
                            details["result_id"] = result.id
                        if hasattr(result, "name"):
                            details["result_name"] = result.name

                    # 标记请求已处理
                    if request is not None:
                        request.state.audited = True

                    # 创建审计日志
                    await _create_audit_log(
                        audit_db,
                        current_user or "system",
                        operation_type,
                        object_type,
                        resource_id,
                        resource_name,
                        details,
                        request.client.host if request else None,
                    )

                return result

            except Exception as e:
                # 记录错误审计日志
                if audit_db is not None:
                    # 确保有资源名称
                    if resource_id is not None and resource_name is None:
                        resource_name = f"{object_type}_{resource_id}"

                    # 标记请求已处理
                    if request is not None:
                        request.state.audited = True

                    # 准备错误详细信息
                    error_details = data_params.copy()  # 使用保存的 *_data 参数
                    error_details["error"] = str(e)  # 添加错误信息

                    # 创建错误审计日志
                    await _create_audit_log(
                        audit_db,
                        current_user or "system",
                        f"{operation_type}_error",
                        object_type,
                        resource_id,
                        resource_name,
                        error_details,
                        request.client.host if request else None,
                    )

                # 重新抛出异常
                raise

            finally:
                # 数据库连接会在请求结束时自动关闭
                pass

        return cast(F, wrapper)

    return decorator

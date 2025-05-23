"""
OpenAPI service for analyzing and importing OpenAPI specifications.

This module provides functionality to:
1. Analyze OpenAPI JSON files (v2 and v3)
2. Extract API endpoints and their parameters
3. Generate tools based on the extracted information
"""

import json
import logging
import re
from typing import Dict, List, Optional, Any

from sqlalchemy.ext.asyncio import AsyncSession

from api.errors.tool_error import ToolAlreadyExistsError
from api.models.tb_func import TbFunc
from api.models.tb_tool import TbTool
from api.schemas.func_schema import FuncCreate
from api.schemas.openapi_schema import OpenApi, OpenApiEndpoint
from api.schemas.tool_schema import ToolCreate
from api.services.func_service import FuncService
from api.services.tool_service import ToolService

# Get logger
logger = logging.getLogger(__name__)


class OpenApiService:
    """
    Service for analyzing OpenAPI specifications and generating tools.

    This service provides methods to:
    1. analyze_openapi: Parse OpenAPI files and extract API information
    2. import_openapi_tools: Create tools from OpenAPI endpoints

    It supports both OpenAPI v2 (Swagger) and v3 formats, and handles:
    - Path parameters (e.g., /users/{id})
    - Query parameters (e.g., ?page=1&size=10)
    - Body parameters from request bodies
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize OpenAPI service.

        Args:
            db: Database session
        """
        self.db = db
        self.tool_service = ToolService(db)
        self.func_service = FuncService(db)

    async def analyze_openapi(self, file_content: bytes) -> OpenApi:
        """
        Analyze OpenAPI specification file and extract API information.

        This method parses an OpenAPI JSON file (v2 or v3), extracts API endpoints,
        normalizes tool names, and generates parameter schemas. It supports:
        - OpenAPI v2 (Swagger)
        - OpenAPI v3

        Args:
            file_content: OpenAPI specification file content (JSON)

        Returns:
            OpenApi: Analyzed API information including server URL and endpoints

        Raises:
            ValueError: If the file is not a valid OpenAPI specification
        """
        try:
            # Parse JSON content
            openapi_data = json.loads(file_content)

            # Determine OpenAPI version
            openapi_version = openapi_data.get("openapi", openapi_data.get("swagger"))
            is_v3 = openapi_version and openapi_version.startswith("3.")

            # Extract server URL
            server_url = ""
            if is_v3 and "servers" in openapi_data and openapi_data["servers"]:
                server_url = openapi_data["servers"][0].get("url", "")
            elif not is_v3 and "host" in openapi_data:
                # OpenAPI v2 uses host, basePath, and schemes
                host = openapi_data.get("host", "")
                base_path = openapi_data.get("basePath", "")
                scheme = openapi_data.get("schemes", ["https"])[0]
                server_url = f"{scheme}://{host}{base_path}"

            # Extract API endpoints
            apis = []
            paths = openapi_data.get("paths", {})
            for path, path_item in paths.items():
                for method, operation in path_item.items():
                    if method in ["get", "post", "put", "delete"]:  # 只处理这四种方法
                        # 生成工具名称
                        tool_name = self._normalize_tool_name(method, path)

                        # 生成工具描述
                        description = ""
                        if operation.get("summary"):
                            description += operation.get("summary")
                        if operation.get("description"):
                            if description:
                                description += "\n\n"
                            description += operation.get("description")

                        # 处理参数，生成 JSON Schema
                        parameters_schema = self._process_parameters(
                            operation, openapi_data, is_v3
                        )

                        apis.append(
                            OpenApiEndpoint(
                                path=path,
                                method=method,
                                tool=tool_name,  # 添加工具名称
                                description=description,  # 添加工具描述
                                parameters=parameters_schema,  # 使用 JSON Schema 格式的参数
                            )
                        )

            # Sort APIs by tool name in ascending order
            apis.sort(key=lambda api: api.path)

            return OpenApi(
                server=server_url,
                apis=apis,
            )

        except Exception as e:
            logger.error(f"Error analyzing OpenAPI file: {str(e)}")
            raise ValueError(f"Invalid OpenAPI file: {str(e)}")

    async def import_openapi_tools(
        self,
        server: str,
        apis: List[Dict[str, Any]],
        current_user: Optional[str] = None,
    ) -> List[TbTool]:
        """
        Import OpenAPI endpoints as tools.

        This method creates tools from OpenAPI endpoints, including:
        1. Creating the call_open_api function if it doesn't exist
        2. Generating tool code for each API endpoint
        3. Creating and deploying tools with appropriate parameters

        Args:
            server: API server URL (e.g., https://api.example.com)
            apis: List of API endpoints to import (from analyze_openapi result)
            current_user: Username for audit logging

        Returns:
            List[TbTool]: Imported tools
        """
        # First, check if call_open_api function exists or create it
        call_open_api_func = await self._ensure_call_open_api_func(current_user)

        # Import tools
        imported_tools = []

        for api_data in apis:
            try:
                # 获取 API 信息
                method = api_data.method.lower()
                path = api_data.path
                tool_name = api_data.tool
                tool_description = api_data.description or ""
                parameters_schema = api_data.parameters or {
                    "type": "object",
                    "properties": {},
                }

                if not tool_name:
                    # 如果没有提供工具名称，则生成一个
                    tool_name = self._normalize_tool_name(method, path)

                if not tool_description:
                    # 如果没有提供工具描述，则生成一个
                    tool_description = f"OpenAPI tool for {method} {path}"

                # 生成工具代码
                tool_code = self._generate_tool_code(
                    method, path, parameters_schema, server
                )

                # 生成工具参数
                # 使用参数 schema 作为工具参数
                tool_parameters = parameters_schema

                # Create tool
                tool_data = ToolCreate(
                    name=tool_name,
                    description=tool_description,
                    parameters=tool_parameters,
                    code=tool_code,
                    func_ids=[call_open_api_func.id],
                    config_ids=[],
                )

                tool = await self.tool_service.create_tool(tool_data, current_user)

                # Deploy tool
                await self.tool_service.deploy_tool(
                    tool.id, "Initial import from OpenAPI", current_user
                )

                # Refresh tool
                await self.db.refresh(tool)

                imported_tools.append(tool)

            except ToolAlreadyExistsError:
                logger.warning(f"Tool already exists: {tool_name}")
                continue
            except Exception as e:
                logger.error(f"Error importing tool {tool_name}: {str(e)}")
                continue

        return imported_tools

    async def _ensure_call_open_api_func(
        self, current_user: Optional[str] = None
    ) -> TbFunc:
        """
        Ensure the call_open_api function exists or create it.

        This method checks if the call_open_api function already exists in the database.
        If not, it creates a new function with the necessary code to call OpenAPI endpoints.

        The call_open_api function is a utility function that handles:
        - Making HTTP requests with different methods (GET, POST, PUT, DELETE)
        - Handling query parameters, headers, and request body
        - Error handling and response parsing

        Args:
            current_user: Username for audit logging if a new function is created

        Returns:
            TbFunc: The existing or newly created call_open_api function
        """
        # Check if function already exists
        func = await self.func_service.get_func_by_name("call_open_api")
        if func:
            return func

        # Create function
        func_code = """import requests
import json
from typing import Dict, Any, Optional

def call_open_api(
    method: str,
    url: str,
    query: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    body: Optional[Dict[str, Any]] = None,
    timeout: int = 30
) -> Dict[str, Any]:
    \"\"\"
    Call an OpenAPI endpoint.

    Args:
        method: HTTP method (get, post, put, delete, patch)
        url: Full URL including server and path
        query: Query parameters
        headers: Request headers
        body: Request body
        timeout: Request timeout in seconds

    Returns:
        Dict[str, Any]: Response data
    \"\"\"
    # Initialize headers if None
    if headers is None:
        headers = {}

    # Make the request
    try:
        response = requests.request(
            method=method,
            url=url,
            params=query,
            headers=headers,
            json=body if body else None,
            timeout=timeout
        )

        # Raise for HTTP errors
        response.raise_for_status()

        # Try to parse JSON response
        try:
            return response.json()
        except ValueError:
            # Return text response if not JSON
            return {"text": response.text}

    except requests.exceptions.RequestException as e:
        return {
            "error": True,
            "message": str(e),
            "status_code": getattr(e.response, "status_code", None) if hasattr(e, "response") else None
        }
"""

        func_data = FuncCreate(
            name="call_open_api",
            description="Call an OpenAPI endpoint",
            code=func_code,
        )

        return await self.func_service.create_func(func_data, current_user)

    def _normalize_tool_name(self, method: str, path: str) -> str:
        """
        Normalize tool name by replacing non-alphanumeric characters with underscores
        and removing leading/trailing/consecutive underscores.

        Args:
            method: HTTP method (get, post, put, delete)
            path: API path (e.g., /users/{id}/profile)

        Returns:
            str: Normalized tool name (e.g., get_users_id_profile)
        """
        # 将所有非字母数字字符替换为下划线
        encoded_path = re.sub(r"[^a-zA-Z0-9]", "_", path)

        # 生成初始工具名
        tool_name = f"{method}_{encoded_path}"

        # 移除前后下划线并将连续下划线替换为单个下划线
        tool_name = re.sub(r"_+", "_", tool_name).strip("_")

        return tool_name

    def _process_parameters(
        self, operation: Dict[str, Any], openapi_data: Dict[str, Any], is_v3: bool
    ) -> Dict[str, Any]:
        """
        Process API parameters and generate JSON Schema.

        Args:
            operation: API operation data
            openapi_data: Full OpenAPI data
            is_v3: Whether the OpenAPI version is v3

        Returns:
            Dict[str, Any]: JSON Schema of parameters
        """
        # 准备参数的 JSON Schema
        parameters_schema = {"type": "object", "properties": {}, "required": []}

        # 处理 API 参数
        parameters = operation.get("parameters", [])

        for param in parameters:
            # 获取参数的基本信息
            param_name = param.get("name")
            param_description = param.get("description", "")
            param_required = param.get("required", False)
            param_schema = param.get("schema", {"type": param.get("type", "string")})
            param_location = param.get("in")

            # 如果参数已存在，合并位置信息
            if param_name in parameters_schema["properties"]:
                existing_param = parameters_schema["properties"][param_name]
                existing_locations = existing_param.get("locations", [])

                # 添加新位置到现有位置列表
                if param_location not in existing_locations:
                    existing_locations.append(param_location)
                    existing_param["locations"] = existing_locations

                # 更新描述，合并不同位置的描述
                location_desc = f"{param_description}"
                if existing_param.get("description"):
                    existing_param["description"] += f"; {location_desc}"
                else:
                    existing_param["description"] = location_desc
            else:
                # 创建新参数
                param_info = {
                    "type": param_schema.get("type", "string"),
                    "description": f"{param_description}",
                    "locations": [param_location],  # 使用 locations 数组
                }

                # 复制其他 schema 属性
                for key, value in param_schema.items():
                    if key not in ["type"]:
                        param_info[key] = value

                parameters_schema["properties"][param_name] = param_info

            # 处理必需参数
            if param_required and param_name not in parameters_schema["required"]:
                parameters_schema["required"].append(param_name)

            # Handle body parameters (OpenAPI v2) - 特殊处理
            if param.get("in") == "body":
                schema = param.get("schema", {})

                # Resolve $ref if present
                if "$ref" in schema:
                    ref_schema = self._resolve_ref(schema["$ref"], openapi_data)
                    schema = ref_schema if ref_schema else schema

                # 确保 schema 包含 properties
                if not isinstance(schema, dict) or "properties" not in schema:
                    logger.warning(
                        f"Body parameter schema does not contain properties: {schema}"
                    )
                    schema = {"properties": {}}

                # 处理 body 参数中的每个属性
                if "properties" in schema and isinstance(schema["properties"], dict):
                    for prop_name, prop_schema in schema["properties"].items():
                        # 如果属性已存在，合并位置信息
                        if prop_name in parameters_schema["properties"]:
                            existing_param = parameters_schema["properties"][prop_name]
                            existing_locations = existing_param.get("locations", [])

                            if "body" not in existing_locations:
                                existing_locations.append("body")
                                existing_param["locations"] = existing_locations
                        else:
                            # 添加到 JSON Schema
                            parameters_schema["properties"][prop_name] = {
                                **prop_schema,
                                "description": f"{prop_schema.get('description', '')}",
                                "locations": ["body"],  # 使用 locations 数组
                            }

                        # 如果是必需参数
                        if param.get("required", False) and prop_name in schema.get(
                            "required", []
                        ):
                            if prop_name not in parameters_schema["required"]:
                                parameters_schema["required"].append(prop_name)

        # Process requestBody (OpenAPI v3)
        if is_v3 and "requestBody" in operation:
            self._process_request_body(
                operation.get("requestBody", {}), parameters_schema, openapi_data
            )

        # 如果没有必需参数，则不添加 required 字段
        if not parameters_schema["required"]:
            del parameters_schema["required"]

        return parameters_schema

    def _generate_tool_code(
        self,
        method: str,
        path: str,
        parameters_schema: Dict[str, Any],
        server: str,
    ) -> str:
        """
        Generate tool code for OpenAPI endpoint.

        This method generates Python code that uses the call_open_api function
        to call an API endpoint. The generated code handles:
        - Path parameters (replacing {param} in the URL)
        - Query parameters (adding to the URL query string)
        - Body parameters (adding to the request body)

        Args:
            method: HTTP method (get, post, put, delete)
            path: API path (e.g., /users/{id})
            parameters_schema: JSON Schema of parameters with locations metadata
            server: API server URL (e.g., https://api.example.com)

        Returns:
            str: Generated Python code for the tool
        """
        # Remove trailing slash from server
        if server.endswith("/"):
            server = server[:-1]

        code = f"""# This tool was auto-generated from OpenAPI
# Method: {method.upper()}, Path: {path}

# API server and path configuration
api_server = "{server}"
api_path = "{path}"
api_method = "{method}"

# Initialize parameter containers
query = {{}}
body = {{}}

# Process input parameters
"""

        # 处理参数
        if "properties" in parameters_schema:
            for param_name, param_schema in parameters_schema["properties"].items():
                param_locations = param_schema.get("locations", [])

                # 处理每个位置
                for location in param_locations:
                    if location == "query":
                        code += f"# 处理 query 参数: {param_name}\n"
                        code += f'if "{param_name}" in parameters:\n'
                        code += f'    query["{param_name}"] = parameters.get("{param_name}")\n\n'

                    elif location == "path":
                        # path 参数直接替换到 api_path 中
                        code += f"# 处理 path 参数: {param_name}\n"
                        code += f'if "{param_name}" in parameters:\n'
                        code += f'    api_path = api_path.replace("{{{param_name}}}", str(parameters.get("{param_name}")))\n\n'

                    elif location == "body":
                        code += f"# 处理 body 参数: {param_name}\n"
                        code += f'if "{param_name}" in parameters:\n'
                        code += f'    body["{param_name}"] = parameters.get("{param_name}")\n\n'

        # 添加调用 API 的代码
        code += f"""
# Get headers from config if available
headers = {{}}
if config and "headers" in config:
    headers = config.get("headers", {{}})

# Call the API
response = call_open_api(
    method=api_method,
    url=f"{{api_server}}{{api_path}}",
    query=query,
    headers=headers,
    body=body if body else None,
    timeout=30
)

# Set the result
result = response
"""
        return code

    def _process_request_body(
        self,
        req_body: Dict[str, Any],
        parameters_schema: Dict[str, Any],
        openapi_data: Dict[str, Any],
    ) -> None:
        """
        Process request body (OpenAPI v3).

        Args:
            req_body: Request body data
            parameters_schema: Parameters schema to update
            openapi_data: Full OpenAPI data
        """
        content = req_body.get("content", {})

        # Only support application/json
        if "application/json" in content:
            json_content = content["application/json"]
            schema = json_content.get("schema", {})

            # Resolve $ref if present
            if "$ref" in schema:
                ref_path = schema["$ref"]
                ref_schema = self._resolve_ref(ref_path, openapi_data)
                schema = ref_schema if ref_schema else schema

            # 确保 schema 包含 properties
            if not isinstance(schema, dict) or "properties" not in schema:
                logger.warning(
                    f"RequestBody schema does not contain properties: {schema}"
                )
                schema = {"properties": {}}

            # 处理 requestBody 中的每个属性
            if "properties" in schema and isinstance(schema["properties"], dict):
                for prop_name, prop_schema in schema["properties"].items():
                    # 如果属性已存在，合并位置信息
                    if prop_name in parameters_schema["properties"]:
                        existing_param = parameters_schema["properties"][prop_name]
                        existing_locations = existing_param.get("locations", [])

                        if "body" not in existing_locations:
                            existing_locations.append("body")
                            existing_param["locations"] = existing_locations

                        # 更新描述
                        body_desc = (
                            f"Body parameter: {prop_schema.get('description', '')}"
                        )
                        if existing_param.get("description"):
                            existing_param["description"] += f"; {body_desc}"
                        else:
                            existing_param["description"] = body_desc
                    else:
                        # 添加到 JSON Schema
                        parameters_schema["properties"][prop_name] = {
                            **prop_schema,
                            "description": f"Body parameter: {prop_schema.get('description', '')}",
                            "locations": ["body"],  # 使用 locations 数组
                        }

                    # 如果是必需参数
                    if req_body.get("required", False) and prop_name in schema.get(
                        "required", []
                    ):
                        if prop_name not in parameters_schema["required"]:
                            parameters_schema["required"].append(prop_name)

    def _resolve_ref(self, ref_path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve $ref reference in OpenAPI specification.

        This method handles references in both OpenAPI v2 and v3 formats:
        - v2: #/definitions/Schema
        - v3: #/components/schemas/Schema

        It also handles nested references by recursively resolving them.

        Args:
            ref_path: Reference path (e.g., "#/definitions/User" or "#/components/schemas/User")
            data: Full OpenAPI specification data

        Returns:
            Dict[str, Any]: Resolved schema or empty dict if reference cannot be resolved
        """
        # Only handle local references
        if not ref_path.startswith("#/"):
            logger.warning(f"External references not supported: {ref_path}")
            return {}

        # Split the reference path into parts
        parts = ref_path[2:].split("/")
        current = data

        # Navigate through the reference path
        for part in parts:
            if part in current:
                current = current[part]
            else:
                logger.warning(
                    f"Could not resolve reference part '{part}' in path '{ref_path}'"
                )
                return {}

        # Handle nested references
        if isinstance(current, dict) and "$ref" in current:
            # Prevent infinite recursion
            if current["$ref"] == ref_path:
                logger.warning(f"Circular reference detected: {ref_path}")
                return current

            return self._resolve_ref(current["$ref"], data)

        return current

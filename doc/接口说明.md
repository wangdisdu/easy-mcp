# Easy MCP API 接口文档

## 基础信息

- 基础URL: `/api/v1`
- 认证方式: Bearer Token (JWT)
- 响应格式: JSON

## 代码规范

- API 目录下的 Python 代码应遵循 `@api/STANDARDIZATION.md` 中定义的代码标准
- 保持一致的命名风格、注释和文档字符串格式
- 使用统一的错误处理和响应格式

## 通用响应格式

```json
{
    "code": 0,           // 0表示成功，非0表示错误
    "message": "success", // 响应消息
    "data": {},          // 响应数据，如果是分页查询这里是数组
    "total": 1           // 数据总数，如果是分页查询，返回total
}
```

## 认证相关接口

### 用户登录

- **URL**: `/auth/login`
- **方法**: POST
- **描述**: 用户登录接口
- **请求体**:
```json
{
    "username": "string",
    "password": "string"
}
```
- **响应**:
```json
{
    "code": 0,
    "message": "success",
    "data": {
        "token": "string"
    }
}
```

### 查询用户列表

- **URL**: `/user`
- **方法**: GET
- **描述**: 获取用户列表
- **查询参数**:
  - `page`: 页码（默认1）
  - `size`: 每页数量（默认20）
  - `search`: 用户名或邮箱（可选，模糊查询）
- **响应**:
```json
{
    "code": 0,
    "message": "success",
    "data": [],
    "total": 0
}
```

### 创建用户

- **URL**: `/user`
- **方法**: POST
- **描述**: 创建新用户
- **请求体**:
```json
{
    "username": "string",
    "password": "string",
    "email": "string"
}
```
- **响应**: 通用响应格式

### 查询用户详情

- **URL**: `/user/{user_id}`
- **方法**: GET
- **描述**: 获取指定用户信息
- **响应**: 通用响应格式

### 更新用户

- **URL**: `/user/{user_id}`
- **方法**: PUT
- **描述**: 更新用户信息
- **请求体**:
```json
{
    "email": "string",
    "password": "string"  // 可选，如果提供则更新密码
}
```
- **响应**: 通用响应格式

### 删除用户

- **URL**: `/user/{user_id}`
- **方法**: DELETE
- **描述**: 删除指定用户
- **响应**: 通用响应格式

## 工具管理接口

### 获取工具列表

- **URL**: `/tool`
- **方法**: GET
- **描述**: 获取所有工具列表
- **查询参数**:
  - `page`: 页码（默认1）
  - `size`: 每页数量（默认20）
  - `search`: 名称或描述（可选，模糊查询）
- **响应**:
```json
{
    "code": 0,
    "message": "success",
    "data": [],
    "total": 0
}
```

### 创建工具

- **URL**: `/tool`
- **方法**: POST
- **描述**: 创建新工具
- **请求体**:
```json
{
    "name": "string",
    "description": "string",
    "parameters": {
        "type": "object",
        "properties": {}
    },
    "code": "string",
    "config_ids": [],
    "func_ids": []
}
```
- **响应**: 通用响应格式

### 创建并发布工具

- **URL**: `/tool/deploy`
- **方法**: POST
- **描述**: 创建新工具并发布
- **请求体**: 同创建工具
- **响应**: 通用响应格式

### 更新工具

- **URL**: `/tool/{tool_id}`
- **方法**: PUT
- **描述**: 更新工具信息
- **请求体**: 同创建工具
- **响应**: 通用响应格式

### 更新并发布工具

- **URL**: `/tool/{tool_id}/deploy`
- **方法**: PUT
- **描述**: 更新工具信息并发布
- **请求体**: 同创建工具
- **响应**: 通用响应格式

### 工具发布历史

- **URL**: `/tool/{tool_id}/deploy/history`
- **方法**: GET
- **描述**: 获取工具发布历史
- **查询参数**:
  - `page`: 页码
  - `size`: 每页数量
- **响应**:
```json
{
    "code": 0,
    "message": "success",
    "data": [],
    "total": 0
}
```

### 回退工具版本

- **URL**: `/tool/{tool_id}/deploy/rollback/{version}`
- **方法**: POST
- **描述**: 回退工具到指定版本
- **响应**: 通用响应格式

### 删除工具

- **URL**: `/tool/{tool_id}`
- **方法**: DELETE
- **描述**: 删除指定工具
- **响应**: 通用响应格式

### 工具调试

- **URL**: `/tool/{tool_id}/debug`
- **方法**: POST
- **描述**: 调试工具执行
- **请求体**:
```json
{
    "parameters": {}
}
```
- **响应**:
```json
{
    "code": 0,
    "message": "success",
    "data": {
        "success": true,
        "result": {},
        "error": null
    }
}
```

## 函数管理接口

### 获取函数列表

- **URL**: `/func`
- **方法**: GET
- **描述**: 获取所有函数列表
- **查询参数**:
  - `page`: 页码
  - `size`: 每页数量
  - `search`: 名称或描述（可选，模糊查询）
- **响应**:
```json
{
    "code": 0,
    "message": "success",
    "data": [],
    "total": 0
}
```

### 创建函数

- **URL**: `/func`
- **方法**: POST
- **描述**: 创建新的函数
- **请求体**:
```json
{
    "name": "string",
    "description": "string",
    "code": "string",
    "depend_ids": []
}
```
- **响应**: 通用响应格式

### 创建并发布函数

- **URL**: `/func/deploy`
- **方法**: POST
- **描述**: 创建新的函数并发布
- **请求体**: 同创建函数
- **响应**: 通用响应格式

### 更新函数

- **URL**: `/func/{func_id}`
- **方法**: PUT
- **描述**: 更新函数信息
- **请求体**: 同创建函数
- **响应**: 通用响应格式

### 更新并发布函数

- **URL**: `/func/{func_id}/deploy`
- **方法**: PUT
- **描述**: 更新函数信息并发布
- **请求体**: 同创建函数
- **响应**: 通用响应格式

### 函数发布历史

- **URL**: `/func/{func_id}/deploy/history`
- **方法**: GET
- **描述**: 获取函数发布历史
- **查询参数**:
  - `page`: 页码
  - `size`: 每页数量
- **响应**:
```json
{
    "code": 0,
    "message": "success",
    "data": [],
    "total": 0
}
```

### 回退函数版本

- **URL**: `/func/{func_id}/deploy/rollback/{version}`
- **方法**: POST
- **描述**: 回退函数到指定版本
- **响应**: 通用响应格式

### 删除函数

- **URL**: `/func/{func_id}`
- **方法**: DELETE
- **描述**: 删除指定函数
- **响应**: 通用响应格式

## 配置管理接口

### 获取配置列表

- **URL**: `/config`
- **方法**: GET
- **描述**: 获取所有配置列表
- **查询参数**:
  - `page`: 页码（默认1）
  - `size`: 每页数量（默认20）
  - `search`: 名称或描述（可选，模糊查询）
- **响应**:
```json
{
    "code": 0,
    "message": "success",
    "data": [],
    "total": 0
}
```

### 创建配置

- **URL**: `/config`
- **方法**: POST
- **描述**: 创建新的配置
- **请求体**:
```json
{
    "name": "string",
    "description": "string",
    "conf_schema": {}
}
```
- **响应**: 通用响应格式

### 获取配置详情

- **URL**: `/config/{config_id}`
- **方法**: GET
- **描述**: 获取指定配置信息
- **响应**: 通用响应格式

### 更新配置

- **URL**: `/config/{config_id}`
- **方法**: PUT
- **描述**: 更新配置信息
- **请求体**: 同创建配置
- **响应**: 通用响应格式

### 删除配置

- **URL**: `/config/{config_id}`
- **方法**: DELETE
- **描述**: 删除指定配置
- **响应**: 通用响应格式

## 资源关系接口

### 获取配置使用情况

- **URL**: `/config/{config_id}/usage`
- **方法**: GET
- **描述**: 获取使用该配置的工具列表
- **响应**: 通用响应格式，数据中包含工具列表

### 获取函数使用情况

- **URL**: `/func/{func_id}/usage`
- **方法**: GET
- **描述**: 获取使用该函数的工具和依赖该函数的其他函数
- **响应**: 通用响应格式，数据中包含工具列表和函数列表

### 获取函数依赖关系

- **URL**: `/func/{func_id}/depend`
- **方法**: GET
- **描述**: 获取函数的依赖关系
- **响应**: 通用响应格式，数据中包含被依赖的函数列表

### 获取工具关联的配置

- **URL**: `/tool/{tool_id}/config`
- **方法**: GET
- **描述**: 获取工具关联的配置
- **响应**: 通用响应格式，数据中包含配置列表

### 获取工具关联的函数

- **URL**: `/tool/{tool_id}/func`
- **方法**: GET
- **描述**: 获取工具关联的函数
- **响应**: 通用响应格式，数据中包含函数列表

## 工具启用/禁用接口

### 启用工具

- **URL**: `/tool/{tool_id}/enable`
- **方法**: POST
- **描述**: 启用指定工具
- **响应**: 通用响应格式

### 禁用工具

- **URL**: `/tool/{tool_id}/disable`
- **方法**: POST
- **描述**: 禁用指定工具
- **响应**: 通用响应格式
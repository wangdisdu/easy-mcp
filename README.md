# Easy MCP

Easy MCP 是一个动态 MCP (Model Context Protocol) 工具注册服务器，允许用户创建、管理和调试 MCP 工具。该项目使用 Python 3.12、FastAPI 和 Vue3 构建，提供了一个完整的工具管理系统，包括函数代码编辑、工具调试、配置管理等功能。

## 功能特点

- **MCP 服务器**: 实现 MCP 协议的服务器，提供 SSE (Server-Sent Events) 服务
- **工具管理**: 维护工具的参数、描述和实现代码等信息，支持版本控制
- **函数管理**: 管理工具依赖的的函数代码库，支持版本控制
- **配置管理**: 管理工具的配置信息
- **用户管理**: 管理用户账户和认证
- **审计日志**: 记录用户在系统中的操作日志，主要记录变更操作

## 技术栈

### 后端

- **Python 3.12**: 核心编程语言
- **FastAPI + Starlette + Uvicorn**: Web 框架和服务器
- **SQLModel**: ORM 框架（基于 SQLAlchemy 和 Pydantic）
- **MCP**: Model Context Protocol 库

### 前端

- **Vue 3**: 前端框架
- **Ant Design Vue**: UI 组件库
- **Vue Router**: 路由管理
- **Axios**： HTTP 请求库
- **Pinia**: 状态管理

## 快速开始

### 环境要求

- Python 3.12+
- Node.js 16+
- npm 8+

### 环境配置

项目使用 `.env` 文件进行配置。复制 `.env.example` 文件并根据需要修改：

```bash
cp .env.example .env
```

主要配置项包括：

- 数据库连接 (DB_URL)
- JWT 密钥 (JWT_SECRET_KEY)
- 服务器设置 (HOST, PORT)
- 管理员账户 (ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_EMAIL)

### 后端设置

1. 进入 api 目录：

```bash
cd api
```

2. 创建虚拟环境：

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

3. 安装依赖：

```bash
pip install -r requirements.txt
```

4. 运行服务器：

```bash
uvicorn api.main:app --reload
```

服务器将在 http://localhost:8000 上运行，API 文档可在 http://localhost:8000/docs 查看。

### 前端设置

1. 进入 frontend 目录：

```bash
cd frontend
```

2. 安装依赖：

```bash
npm install
```

3. 运行开发服务器：

```bash
npm run dev
```

前端将在 http://localhost:5173 上运行。

### 使用 Docker 运行

项目提供了 Docker 配置，可以使用 Docker Compose 快速启动整个系统：

```bash
docker-compose up -d
```

这将启动以下服务：

- API 服务器 (http://localhost:8000)
- PostgreSQL 数据库
- 前端应用 (http://localhost:80)

## 项目结构

```
easy-mcp/
├── api/                  # 后端代码
│   ├── config.py         # 应用配置
│   ├── database.py       # 数据库连接和会话管理
│   ├── main.py           # 应用入口点
│   ├── requirements.txt  # 依赖项
│   ├── errors/           # 错误类定义
│   ├── middleware/       # 中间件
│   ├── models/           # 数据库模型
│   ├── routers/          # API 路由
│   ├── schemas/          # Pydantic 模型/架构
│   ├── services/         # 业务逻辑服务
│   └── utils/            # 工具函数
├── frontend/             # 前端代码
│   ├── public/           # 静态资源
│   ├── src/              # 源代码
│   │   ├── components/   # 公共组件
│   │   ├── router/       # 路由配置
│   │   ├── stores/       # Pinia 状态管理
│   │   ├── utils/        # 工具函数
│   │   ├── views/        # 页面组件
│   │   ├── App.vue       # 根组件
│   │   └── main.js       # 应用入口
│   ├── package.json      # 项目依赖
│   └── vite.config.js    # Vite 配置
├── .env.example          # 环境变量示例
├── .env                  # 环境变量配置
├── Dockerfile            # API Docker 配置
├── docker-compose.yml    # Docker Compose 配置
└── README.md             # 项目说明
```

## 数据库模型

系统使用 SQLModel 作为 ORM 框架，主要数据表包括：

- **tb_user**: 用户表
- **tb_tool**: 工具表
- **tb_tool_deploy**: 工具发布历史表
- **tb_tool_func**: 工具函数表
- **tb_tool_config**: 工具配置表
- **tb_func**: 函数库表
- **tb_func_deploy**: 函数发布历史表
- **tb_func_depends**: 函数依赖关系表
- **tb_config**: 配置表
- **tb_audit**: 审计日志表

## API 接口

API 接口遵循 RESTful 风格，主要包括：

- **/api/v1/auth**: 认证相关接口
- **/api/v1/user**: 用户管理接口
- **/api/v1/tool**: 工具管理接口
- **/api/v1/func**: 函数管理接口
- **/api/v1/config**: 配置管理接口
- **/api/v1/audit**: 审计日志接口
- **/api/v1/sse**: MCP SSE 接口
- **/api/v1/invoke**: MCP 工具调用接口

详细的 API 文档可在运行后端服务器后访问 http://localhost:8000/docs 查看。

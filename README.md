# Easy MCP

Easy MCP 是一个动态 MCP (Model Context Protocol) 工具注册服务器，允许用户创建、管理和调试 MCP 工具。该项目使用 Python 3.12、FastAPI 和 Vue3 构建，提供了一个完整的工具管理系统，包括函数代码编辑、工具调试、配置管理等功能。

## 为什么

MCP (Model Context Protocol) 已经成为AI大模型领域的标准协议，它为AI模型与外部工具的交互提供了统一的接口规范。随着大模型应用场景的不断扩展，开发者需要频繁地创建、更新和管理各种MCP工具，以满足不断变化的业务需求。

然而，传统的MCP Server开发流程存在诸多痛点：

- **开发成本高**：需要从零开始构建MCP Server项目，包括服务器架构、API设计、工具注册等
- **迭代周期长**：每次需求变更都需要修改代码、重新编译、重新部署整个服务
- **运维复杂**：工具管理、版本控制、配置管理等需要额外开发
- **响应速度慢**：无法快速适应业务需求的变化，影响产品迭代和用户体验
- **开发门槛高**：需要掌握完整的MCP协议实现和服务器开发知识

这些问题严重制约了AI大模型能力的快速落地和应用创新。Easy MCP正是为解决这些痛点而生，旨在提供一种更简单、更灵活、更高效的方式来构建和管理MCP工具生态。

## 是什么

Easy MCP 是一个动态MCP工具管理平台，它彻底简化了MCP Server的开发和维护流程。

通过Easy MCP，您可以：

- **快速开发**：只需编写简单的Python函数代码，无需关心底层MCP协议实现
- **即时生效**：代码修改后立即发布，无需重启服务，实现热更新
- **可视化管理**：通过直观的Web界面管理工具、函数和配置
- **版本控制**：内置函数版本管理，支持一键回滚
- **配置灵活**：分离代码与配置，支持动态配置调整
- **依赖管理**：支持函数间依赖关系，促进代码复用
- **完整生态**：提供用户管理、审计日志、调试工具等全套功能

简而言之，Easy MCP将传统的“编码-编译-部署”流程简化为“编写-发布”两步操作，显著提升了开发效率和响应速度，让开发者能够专注于业务逻辑实现，而非底层架构搭建。

## 怎么用

Easy MCP 提供了直观的界面和简单的操作流程，让您能够快速上手并开发自己的MCP工具。下面我们将通过详细的步骤指南，帮助您了解如何使用Easy MCP的核心功能。

### 快速入门

#### 1. 启动服务

参考《快速开始.md》，启动Easy MCP服务。

#### 2. 登录系统

- 打开浏览器，访问 `http://localhost:8000`
- 使用默认管理员账户登录（用户名：`admin`，密码：`admin`）

### 导入内置工具示例

我们先通过导入内置的天气查询工具来快速体验Easy MCP的功能：

#### 1. 导入工具

- 登录后进入「工具管理」页面
- 点击右上角的「导入工具」按钮
- 在弹出的对话框中选择「天气查询工具」
- 点击「导入」按钮完成导入

导入过程会自动创建以下三个组件：

- **天气查询工具**：一个完整的MCP工具，包含名称、描述和参数定义
- **天气查询函数**：实现天气查询逻辑的Python函数代码
- **API密钥配置**：用于存储高德地图API密钥的配置项

#### 2. 配置API密钥

- 导航到「配置管理」页面
- 找到名为「高德地图API密钥」的配置项
- 点击「编辑」按钮
- 在配置值中填入您从[高德开放平台](https://lbs.amap.com/)申请的API密钥
- 点击「保存」按钮

#### 3. 调试工具

- 返回「工具管理」页面
- 找到「天气查询工具」
- 点击「调试」按钮
- 在参数输入框中填入城市名称（如「北京」）
- 点击「执行」按钮
- 查看执行结果和输出信息

#### 4. 接入Cherry Studio

现在你可以将工具集成到Cherry Studio中，实现基于MCP的工具化开发。

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

## 开发环境

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

项目提供了完整的 Docker 配置，支持三种数据库后端：

```bash
# 使用 CLI 工具（推荐）
./easy-mcp.sh deploy                    # SQLite 部署
./easy-mcp.sh -d postgres deploy        # Postgres 部署
./easy-mcp.sh -d mysql deploy           # MySQL 部署

# 或使用 Makefile
make deploy                              # SQLite 部署
make deploy DB_TYPE=postgres             # Postgres 部署
```

这将启动以下服务：

- API 服务器 (http://localhost:8000)
- 数据库服务（根据选择的类型）
- 前端应用（集成在API服务中）

## 项目结构

```
easy-mcp/
├── api/                              # 后端代码
│   ├── config.py                     # 应用配置
│   ├── database.py                   # 数据库连接和会话管理
│   ├── main.py                       # 应用入口点
│   ├── requirements.txt              # 依赖项
│   ├── errors/                       # 错误类定义
│   ├── middleware/                   # 中间件
│   ├── models/                       # 数据库模型
│   ├── routers/                      # API 路由
│   ├── schemas/                      # Pydantic 模型/架构
│   ├── services/                     # 业务逻辑服务
│   └── utils/                        # 工具函数
├── frontend/                         # 前端源代码
│   ├── public/                       # 静态资源
│   ├── src/                          # 源代码
│   │   ├── components/               # 公共组件
│   │   ├── router/                   # 路由配置
│   │   ├── stores/                   # Pinia 状态管理
│   │   ├── utils/                    # 工具函数
│   │   ├── views/                    # 页面组件
│   │   ├── App.vue                   # 根组件
│   │   └── main.js                   # 应用入口
│   ├── package.json                  # 项目依赖
│   └── vite.config.js                # Vite 配置
├── static/                           # 前端构建文件
├── docker/                           # Docker 配置目录
│   ├── Dockerfile                    # Docker 镜像构建文件
│   ├── docker-compose.*.yml          # 各数据库部署配置
│   └── .env.*                        # 环境变量配置
├── doc/                              # 文档目录
│   ├── Docker说明.md                 # Docker 部署说明
│   ├── 接口说明.md                   # API 接口文档
│   ├── 数据库设计.md                 # 数据库设计文档
│   └── 系统设计.md                   # 系统架构设计
├── scripts/                          # 脚本目录
├── data/                             # SQLite 数据目录
├── logs/                             # 日志目录
├── backup/                           # 备份目录
├── easy-mcp.sh                       # CLI 管理工具
├── Makefile                          # Make 命令工具
├── 快速开始.md                       # 快速开始指南
└── README.md                         # 项目说明
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

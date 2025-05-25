# Easy MCP Docker 部署说明

## 🎯 概述

本文档介绍如何使用 Docker 和 Docker Compose 部署 Easy MCP 系统，支持三种数据库后端：SQLite、PostgreSQL 和 MySQL。

> **重要说明**: 所有 Docker 相关文件已统一放置在 `docker/` 目录下，另外请确保 `static/` 目录包含前端构建文件。

## 📁 文件结构

```
easy-mcp/
├── docker/                           # Docker 配置目录
│   ├── Dockerfile                    # Docker 镜像构建文件
│   ├── docker-compose.sqlite.yml     # SQLite 部署配置
│   ├── docker-compose.postgres.yml   # PostgreSQL 部署配置
│   ├── docker-compose.mysql.yml      # MySQL 部署配置
│   ├── .env.sqlite                   # SQLite 环境变量
│   ├── .env.postgres                 # PostgreSQL 环境变量
│   └── .env.mysql                    # MySQL 环境变量
├── scripts/                          # 脚本目录
│   ├── init-postgres.sql             # PostgreSQL 初始化脚本
│   ├── init-mysql.sql                # MySQL 初始化脚本
│   ├── health-check.sh               # 健康检查脚本
│   └── monitor.sh                    # 监控脚本
├── static/                           # 前端静态文件目录
├── data/                             # SQLite 数据目录
├── logs/                             # 日志目录
├── backup/                           # 备份目录
├── easy-mcp.sh                       # 主要 CLI 工具
└── Makefile                          # Make 命令便捷工具
```

## 🚀 快速开始

### 1. 使用 CLI 工具（推荐）

我们提供了 `easy-mcp.sh` CLI 工具来简化部署过程：

```bash
# 查看帮助
./easy-mcp.sh --help

# 使用 SQLite 部署（默认）
./easy-mcp.sh deploy

# 使用 Postgres 部署
./easy-mcp.sh -d postgres deploy

# 使用 MySQL 部署
./easy-mcp.sh -d mysql deploy
```

### 2. 使用 Makefile

```bash
make deploy                    # SQLite 部署
make deploy DB_TYPE=postgres   # Postgres 部署
make deploy DB_TYPE=mysql      # MySQL 部署
```

### 3. 手动部署

如果您更喜欢手动控制部署过程：

```bash
# SQLite 部署
docker-compose -f docker/docker-compose.sqlite.yml build
docker-compose -f docker/docker-compose.sqlite.yml up -d

# Postgres 部署
docker-compose -f docker/docker-compose.postgres.yml build
docker-compose -f docker/docker-compose.postgres.yml up -d

# MySQL 部署
docker-compose -f docker/docker-compose.mysql.yml build
docker-compose -f docker/docker-compose.mysql.yml up -d
```

## 🔧 CLI 工具使用说明

### 基本命令

| 命令 | 功能 | 示例 |
|------|------|------|
| `build` | 构建镜像 | `./easy-mcp.sh build` |
| `deploy` | 部署服务 | `./easy-mcp.sh -d postgres deploy` |
| `start` | 启动服务 | `./easy-mcp.sh start` |
| `stop` | 停止服务 | `./easy-mcp.sh stop` |
| `restart` | 重启服务 | `./easy-mcp.sh restart` |
| `logs` | 查看日志 | `./easy-mcp.sh logs` |
| `status` | 查看状态 | `./easy-mcp.sh status` |
| `health` | 健康检查 | `./easy-mcp.sh health` |
| `clean` | 清理数据 | `./easy-mcp.sh clean` |
| `backup` | 备份数据库 | `./easy-mcp.sh backup` |
| `restore` | 恢复数据库 | `./easy-mcp.sh restore` |

### 指定数据库类型

```bash
# 使用 PostgreSQL
./easy-mcp.sh -d postgres [command]

# 使用 MySQL
./easy-mcp.sh -d mysql [command]

# 使用 SQLite（默认）
./easy-mcp.sh -d sqlite [command]
```

## 🌐 端口映射

| 服务 | 端口 | 说明 |
|------|------|------|
| Easy MCP API | 8000 | 主应用程序端口 |
| PostgreSQL | 5432 | PostgreSQL 数据库端口 |
| MySQL | 3306 | MySQL 数据库端口 |

## 📊 监控和健康检查

### 健康检查
```bash
# 一次性健康检查
./easy-mcp.sh health

# 或直接运行脚本
./scripts/health-check.sh
```

### 持续监控
```bash
# 默认每60秒检查一次
./scripts/monitor.sh

# 自定义监控间隔和邮件告警
./scripts/monitor.sh -i 30 -e admin@example.com
```

## 🔒 环境变量配置

### 通用配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| DEBUG | false | 调试模式 |
| LOG_LEVEL | INFO | 日志级别 |
| HOST | 0.0.0.0 | 服务器主机 |
| PORT | 8000 | 服务器端口 |
| JWT_SECRET_KEY | easy_mcp_production_secret_key_change_me | JWT 密钥 |
| ADMIN_USERNAME | admin | 管理员用户名 |
| ADMIN_PASSWORD | admin123 | 管理员密码 |
| ADMIN_EMAIL | admin@example.com | 管理员邮箱 |

### 数据库配置

#### SQLite
```bash
DB_URL=sqlite+aiosqlite:///./data/easy_mcp.db
```

#### PostgreSQL
```bash
DB_URL=postgresql+asyncpg://easy_mcp:easy_mcp_password@postgres:5432/easy_mcp
POSTGRES_DB=easy_mcp
POSTGRES_USER=easy_mcp
POSTGRES_PASSWORD=easy_mcp_password
```

#### MySQL
```bash
DB_URL=mysql+aiomysql://easy_mcp:easy_mcp_password@mysql:3306/easy_mcp?charset=utf8mb4
MYSQL_ROOT_PASSWORD=root_password
MYSQL_DATABASE=easy_mcp
MYSQL_USER=easy_mcp
MYSQL_PASSWORD=easy_mcp_password
```

## 📝 数据持久化

- **SQLite**: 数据存储在 `./data/easy_mcp.db`
- **PostgreSQL**: 数据存储在 Docker volume `postgres_data`
- **MySQL**: 数据存储在 Docker volume `mysql_data`
- **日志**: 存储在 `./logs/` 目录

## 🔄 备份策略

### SQLite
```bash
# 自动备份
./easy-mcp.sh backup

# 手动备份
cp data/easy_mcp.db backup/manual_backup_$(date +%Y%m%d_%H%M%S).db
```

### PostgreSQL/MySQL
```bash
# PostgreSQL
docker exec easy-mcp-postgres pg_dump -U easy_mcp easy_mcp > backup/postgres_$(date +%Y%m%d_%H%M%S).sql

# MySQL
docker exec easy-mcp-mysql mysqldump -u easy_mcp -peasy_mcp_password easy_mcp > backup/mysql_$(date +%Y%m%d_%H%M%S).sql
```

## 🛠️ 故障排除

### 常见问题

1. **端口冲突**: 检查 8000、5432、3306 端口是否被占用
2. **权限问题**: 确保脚本有执行权限 `chmod +x easy-mcp.sh`
3. **磁盘空间**: 确保有足够的磁盘空间用于数据和日志
4. **内存不足**: 建议至少 8GB 可用内存

### 日志查看
```bash
# 查看所有服务日志
./easy-mcp.sh logs

# 查看特定服务日志
docker-compose -f docker/docker-compose.postgres.yml logs easy-mcp
```

## 🔐 生产环境安全配置

### 必须修改的配置

1. **JWT 密钥**
   ```bash
   JWT_SECRET_KEY=your_secure_random_key_here
   ```

2. **管理员密码**
   ```bash
   ADMIN_PASSWORD=your_secure_password
   ```

3. **数据库密码**
   ```bash
   # PostgreSQL
   POSTGRES_PASSWORD=your_secure_db_password

   # MySQL
   MYSQL_PASSWORD=your_secure_db_password
   MYSQL_ROOT_PASSWORD=your_secure_root_password
   ```

## 🏗️ 开发环境

对于开发环境，建议直接运行后端和前端服务，而不是使用 Docker：

### 后端开发
```bash
# 进入 api 目录
cd api

# 安装依赖
pip install -r requirements.txt

# 运行开发服务器（支持热重载）
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 前端开发
```bash
# 进入 frontend 目录
cd frontend

# 安装依赖
npm install

# 运行开发服务器
npm run dev
```

### Docker 开发环境
如果需要使用 Docker 进行开发，可以直接使用生产配置：

```bash
# 开发环境部署
docker-compose -f docker/docker-compose.sqlite.yml up -d
```

## ✨ 特色功能

1. **一键部署**: 单个命令即可完成整个系统的部署
2. **多数据库支持**: 灵活选择适合的数据库后端
3. **健康监控**: 内置健康检查和监控功能
4. **自动备份**: SQLite 数据库自动备份功能
5. **开发友好**: 支持本地开发和 Docker 部署两种模式
6. **生产就绪**: 包含完整的生产环境配置


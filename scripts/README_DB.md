# 数据库初始化与迁移指南

**版本**: v1.0  
**更新日期**: 2026-02-12  
**适用项目**: 新媒体智能运营平台

---

## 📁 文件说明

```
scripts/
├── init_db.sh              # 数据库初始化脚本 (推荐)
├── init_db.sql             # PostgreSQL 初始化 SQL
├── init_db_sqlite.sql      # SQLite 初始化 SQL
└── README_DB.md            # 本说明文档
```

---

## 🚀 快速开始

### 方式一: 使用自动化脚本 (推荐)

```bash
# 进入项目目录
cd /Users/irvinglu/.openclaw/workspace/xhs_platform

# 方式1: 使用 SQLite (开发环境，无需额外安装)
DB_TYPE=sqlite ./scripts/init_db.sh

# 方式2: 使用 PostgreSQL (生产环境)
DB_TYPE=postgresql \
  DB_HOST=localhost \
  DB_PORT=5432 \
  DB_USER=postgres \
  DB_PASS=postgres \
  DB_NAME=xhs_platform \
  ./scripts/init_db.sh
```

### 方式二: 使用 Docker Compose (全自动)

```bash
# 启动所有服务 (包含自动初始化)
docker-compose up -d

# 数据库会自动创建并初始化
```

### 方式三: 手动执行 SQL

#### PostgreSQL
```bash
# 创建数据库
createdb xhs_platform

# 执行初始化脚本
psql -U postgres -d xhs_platform -f scripts/init_db.sql
```

#### SQLite
```bash
# 创建目录
mkdir -p data

# 初始化数据库
sqlite3 data/xhs_platform.db < scripts/init_db_sqlite.sql
```

---

## 📊 数据库结构

### 表清单

| 表名 | 用途 | 核心字段 |
|------|------|----------|
| `user_preferences` | 用户配置 | persona_config, content_style |
| `hot_topics` | 热点数据 | title, heat_score, category |
| `contents` | 内容数据 | titles, body, status, workflow_id |
| `content_metrics` | 内容指标 | views, likes, comments |
| `workflow_logs` | 工作流日志 | agent_name, action, status |
| `ws_connections` | WebSocket连接 | client_id, connection_status |
| `message_deliveries` | 消息投递 | msg_id, event_type, status |

### ER 图

```
┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│   hot_topics     │         │    contents      │         │  workflow_logs   │
├──────────────────┤         ├──────────────────┤         ├──────────────────┤
│ id (PK)          │◀───────│ topic_id (FK)    │         │ id (PK)          │
│ title            │         │ workflow_id      │◀────────│ workflow_id      │
│ heat_score       │         │ titles[]         │         │ agent_name       │
│ category         │         │ body             │         │ action           │
│ source           │         │ status           │         │ status           │
└──────────────────┘         └──────────────────┘         └──────────────────┘
         │                              │
         │                              │
         ▼                              ▼
┌──────────────────┐         ┌──────────────────┐
│ content_metrics  │         │ message_deliveries│
├──────────────────┤         ├──────────────────┤
│ id (PK)          │         │ id (PK)          │
│ content_id (FK)  │         │ msg_id           │
│ views            │         │ workflow_id      │
│ likes            │         │ event_type       │
└──────────────────┘         └──────────────────┘
```

---

## 🔧 环境配置

### 1. 复制环境变量模板

```bash
cp .env.example .env
```

### 2. 编辑 .env 文件

#### SQLite 配置 (开发)
```bash
DATABASE_URL=sqlite+aiosqlite:///./data/xhs_platform.db
```

#### PostgreSQL 配置 (生产)
```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/xhs_platform
```

### 3. 必需的环境变量

```bash
# 数据库
DATABASE_URL=...

# AI服务 (从 .env 获取)
ARK_API_KEY=xxx
ARK_MODEL_ENDPOINT=xxx
ARK_IMAGE_ENDPOINT=xxx
BRAVE_API_KEY=xxx
```

---

## 🐳 Docker 部署

### 完整启动 (推荐)

```bash
# 1. 克隆项目
git clone <repo-url>
cd xhs_platform

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Key

# 3. 启动所有服务
docker-compose up -d

# 4. 查看状态
docker-compose ps

# 5. 查看日志
docker-compose logs -f api
```

### 仅启动数据库

```bash
# 启动 PostgreSQL + Redis + RabbitMQ
docker-compose up -d postgres redis rabbitmq

# 本地运行 API
cd backend
python -m uvicorn app.main:app --reload
```

---

## 📝 常用操作

### 备份数据库

#### PostgreSQL
```bash
# 备份
pg_dump -U postgres -d xhs_platform > backup_$(date +%Y%m%d).sql

# 恢复
psql -U postgres -d xhs_platform < backup_20260212.sql
```

#### SQLite
```bash
# 备份
cp data/xhs_platform.db backup_$(date +%Y%m%d).db

# 恢复
cp backup_20260212.db data/xhs_platform.db
```

### 清空数据

```bash
# 危险操作！仅用于开发测试
# PostgreSQL
psql -U postgres -d xhs_platform -c "TRUNCATE contents, hot_topics, content_metrics, workflow_logs RESTART IDENTITY;"

# SQLite
sqlite3 data/xhs_platform.db "DELETE FROM contents; DELETE FROM hot_topics;"
```

### 查看表结构

```bash
# PostgreSQL
psql -U postgres -d xhs_platform -c "\dt"
psql -U postgres -d xhs_platform -c "\d contents"

# SQLite
sqlite3 data/xhs_platform.db ".tables"
sqlite3 data/xhs_platform.db ".schema contents"
```

---

## 🔍 故障排查

### 问题1: 数据库连接失败

**现象**: `psycopg2.OperationalError: connection refused`

**解决**:
```bash
# 检查 PostgreSQL 是否运行
docker ps | grep postgres

# 检查端口
lsof -i :5432

# 重启数据库
docker-compose restart postgres
```

### 问题2: 表不存在

**现象**: `sqlalchemy.exc.ProgrammingError: relation "contents" does not exist`

**解决**:
```bash
# 手动执行初始化
./scripts/init_db.sh

# 或在 docker 中执行
docker exec -i xhs_postgres psql -U postgres -d xhs_platform < scripts/init_db.sql
```

### 问题3: 权限错误

**现象**: `permission denied for schema public`

**解决**:
```bash
# PostgreSQL 15+ 需要授予权限
docker exec xhs_postgres psql -U postgres -c "GRANT ALL ON SCHEMA public TO postgres;"
```

---

## 🔄 迁移到生产环境

### 步骤1: 导出开发数据 (可选)

```bash
# SQLite 导出
cd data
sqlite3 xhs_platform.db ".dump" > dump.sql
```

### 步骤2: 生产环境初始化

```bash
# 服务器上
git clone <repo-url>
cd xhs_platform

# 配置生产环境变量
cp .env.example .env
# 编辑 .env: 使用 PostgreSQL，填入生产 API Key

# 启动
docker-compose up -d
```

### 步骤3: 验证

```bash
# 检查服务状态
docker-compose ps

# 检查数据库连接
docker exec xhs_api python -c "from app.core.database import async_engine; print('OK')"

# 测试 API
curl http://localhost/api/v1/contents
```

---

## 📚 相关文档

- [项目架构设计](./ARCHITECTURE.md)
- [API 文档](http://localhost/api/docs) (启动后访问)
- [数据库模型](../backend/app/models/v4_models.py)

---

**维护**: 小珑宝 🤖  
**最后更新**: 2026-02-12

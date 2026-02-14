# 新媒体智能运营平台 - 系统架构设计文档

**版本**: v2.2  
**更新日期**: 2026-02-14  
**状态**: 已上线运行

---

## 1. 架构概览

### 1.1 整体架构图 (Mermaid)

```mermaid
graph TB
    subgraph User["👤 用户层"]
        U1["🌐 Web浏览器"]
        U2["📱 飞书客户端"]
    end

    subgraph Frontend["🖥️ 前端层 Vue3"]
        F1["📊 Dashboard"]
        F2["🔥 热点发现"]
        F3["📋 内容管理"]
        F4["⏰ 定时任务"]
        F5["📜 系统日志"]
    end

    subgraph Gateway["🚪 网关层 Nginx"]
        G1["反向代理"]
        G2["静态资源"]
        G3["负载均衡"]
    end

    subgraph Backend["⚙️ 后端层 FastAPI"]
        API["REST API /api/v1"]
        WS["WebSocket /ws"]
        
        subgraph Core["核心业务"]
            C1["内容管理 API"]
            C2["热点管理 API"]
            C3["定时任务 API"]
            C4["Agent API"]
        end
    end

    subgraph Agents["🤖 AI Agent 层 LangGraph"]
        A1["Orchestrator<br/>工作流总调度"]
        A2["Hotspot Agent<br/>热点获取"]
        A3["Research Agent<br/>热点调研"]
        A4["Creator Agent<br/>内容创作"]
        A5["Compliance Agent<br/>合规检查"]
    end

    subgraph Services["🔧 服务层"]
        S1["Search Service<br/>Brave Search API"]
        S2["LLM Service<br/>豆包大模型"]
        S3["Image Service<br/>即梦图片生成"]
        S4["Feishu Service<br/>飞书通知"]
        S5["MCP Service<br/>小红书API"]
    end

    subgraph Tasks["⏰ 定时任务 Celery"]
        T1["热点追踪<br/>每2小时"]
        T2["账号刷新<br/>每小时"]
        T3["数据抓取<br/>每小时"]
        T4["每日推送<br/>22:00"]
        T5["清理任务<br/>03:00"]
    end

    subgraph Data["💾 数据层"]
        D1[(PostgreSQL<br/>主数据库)]
        D2[(Redis<br/>缓存/队列)]
        D3[(RabbitMQ<br/>消息队列)]
    end

    subgraph External["🔗 外部服务"]
        E1["Brave Search"]
        E2["火山方舟 LLM"]
        E3["即梦 图片"]
        E4["飞书 API"]
        E5["小红书 MCP"]
    end

    U1 --> F1
    U2 --> E4
    
    F1 --> Gateway
    F2 --> Gateway
    F3 --> Gateway
    F4 --> Gateway
    F5 --> Gateway
    
    Gateway --> API
    Gateway --> WS
    
    API --> Core
    Core --> Agents
    Core --> Services
    
    Agents --> Services
    
    Tasks --> Agents
    Tasks --> Services
    
    Services --> External
    
    Backend --> Data
    Tasks --> Data
```

```

### 1.2 技术栈总览

| 层级 | 技术选型 | 版本 | 用途 |
|------|----------|------|------|
| **前端** | Vue 3 | 3.5+ | UI框架 |
| | TypeScript | 5.0+ | 类型安全 |
| | Tailwind CSS | 3.4+ | 原子化CSS |
| | Vite | 5.0+ | 构建工具 |
| | Element Plus | 2.0+ | UI组件库 |
| | ECharts | 5.0+ | 数据可视化 |
| **后端** | FastAPI | 0.104+ | Web框架 |
| | LangGraph | 0.0.40+ | Agent工作流编排 |
| | SQLAlchemy | 2.0+ | ORM |
| | Pydantic | 2.5+ | 数据验证 |
| | Celery | 5.3+ | 定时任务 |
| **AI/ML** | 方舟大模型 (字节) | - | 文本生成 |
| | 即梦 (Seedream) | - | 配图生成 |
| | Brave Search API | - | 实时热点搜索 |
| **数据** | PostgreSQL | 15 | 主数据存储 |
| | Redis | 7 | 缓存、结果后端 |
| | RabbitMQ | - | 消息队列 |
| **部署** | Docker | - | 容器化 |
| | Docker Compose | - | 多服务编排 |
| | Nginx | alpine | 反向代理 |

---

## 2. Agent体系详解

### 2.1 Agent职责矩阵

| Agent | 输入 | 输出 | 调用服务 | 核心能力 |
|-------|------|------|----------|----------|
| **Research Agent** | 用户指令/定时触发 | 热点列表 | Brave Search API | 实时搜索、多源聚合、智能分类 |
| **Compliance Agent** | 热点标题/内容正文 | 合规报告 | 关键词过滤+LLM | 敏感词检测、风险评级、修改建议 |
| **Creator Agent** | 合规热点 | 完整内容 | 方舟大模型+即梦 | 文案生成、配图创作、标签推荐 |
| **Publisher Agent** | 审核通过内容 | 发布包 | MCP服务 | 格式整理、一键复制、状态更新 |

### 2.2 LangGraph 工作流定义 (Mermaid)

```mermaid
stateDiagram-v2
    [*] --> Research: 启动工作流
    
    Research --> ComplianceCheck: 获取热点
    
    ComplianceCheck --> Create: PASS
    ComplianceCheck --> Research: WARNING
    
    Create --> ContentReview: 生成内容
    
    ContentReview --> HumanReview: PASS
    ContentReview --> Create: NEED_FIX
    
    HumanReview --> Publish: APPROVED
    HumanReview --> Create: REJECTED
    
    Publish --> Analytics: 发布成功
    Publish --> [*]: 失败
    
    Analytics --> [*]: 完成
    
    note right of Research
        Research Agent
        - Brave Search搜索热点
        - 热度/专业度/安全度评分
    end note
    
    note right of Create
        Creator Agent
        - LLM生成标题(3个)
        - 生成正文内容
        - 生成配图提示词
    end note
    
    note right of HumanReview
        人工审核节点
        - 飞书通知用户
        - 等待用户决策
        - 通过/拒绝/修改
    end note
```

### 2.3 代码实现

```python
# app/agents/orchestrator.py

from langgraph.graph import StateGraph, END

workflow = StateGraph(WorkflowState)

# 节点定义
workflow.add_node("research", research_node)           # 热点发现
workflow.add_node("compliance_check", compliance_check_node)  # 热点合规
workflow.add_node("create", create_node)              # 内容创作
workflow.add_node("compliance_review", compliance_review_node) # 内容合规
workflow.add_node("review", human_review_node)        # 人工审核
workflow.add_node("publish", publish_node)            # 发布管理
workflow.add_node("analytics", analytics_node)        # 数据分析

# 边定义（流转逻辑）
workflow.set_entry_point("research")
workflow.add_edge("research", "compliance_check")
workflow.add_conditional_edges(
    "compliance_check",
    route_compliance_check,
    {"create": "create", "end": END}
)
workflow.add_edge("create", "compliance_review")
workflow.add_conditional_edges(
    "compliance_review",
    route_compliance_review,
    {"review": "review", "end": END}
)
workflow.add_conditional_edges(
    "review",
    route_review_decision,
    {"publish": "publish", "create": "create", "end": END}
)
workflow.add_edge("publish", "analytics")
workflow.add_edge("analytics", END)
```

---

## 3. 核心服务详解

### 3.1 Search Service (热点搜索)

```python
# app/services/search.py

class HotspotSearchService:
    """实时热点搜索服务"""
    
    async def search_brave(self, query: str, count: int = 10) -> List[Dict]:
        """使用 Brave Search API 搜索"""
        # API: https://api.search.brave.com/res/v1/news/search
        
    async def search_finance_news(self) -> List[Dict]:
        """搜索财经新闻热点"""
        # 关键词池: 央行、LPR、黄金、养老金、数字人民币等
        
    def categorize_topic(self, title: str, summary: str) -> str:
        """热点分类"""
        # 分类: 货币政策、利率、股市、基金、房产、数字货币等
```

**API配置**:
```bash
BRAVE_API_KEY=${BRAVE_API_KEY}  # 从 https://brave.com/search/api/ 获取
```

### 3.2 LLM Service (内容生成)

```python
# app/services/llm.py

class LLMService:
    """大模型服务 - 方舟大模型"""
    
    PERSONA_PROMPT = """你是一位小红书银行博主"银行小姐姐"..."""
    
    async def generate_content(self, topic: dict) -> dict:
        """生成小红书内容"""
        # 输入: {title, summary, category}
        # 输出: {titles[], body, tags[], image_prompts[]}
```

### 3.3 Image Service (配图生成)

```python
# app/services/image.py

class ImageGenerationService:
    """图像生成服务 - 即梦模型"""
    
    async def generate_images(
        self, 
        prompts: List[str], 
        content_id: str,
        width: int = 1024,
        height: int = 1536  # 小红书尺寸
    ) -> List[dict]:
        """生成配图"""
```

### 3.4 MCP Service (小红书API)

```python
# app/services/xhs_mcp.py

class XHSMCPService:
    """小红书 MCP 服务"""
    
    async def get_user_profile(self) -> dict:
        """获取用户账号数据"""
        
    async def get_notes(self, limit: int = 20) -> list:
        """获取笔记列表"""
        
    async def publish_note(self, title: str, content: str, images: list) -> dict:
        """发布笔记"""
```

### 3.5 Feishu Service (飞书通知)

```python
# app/services/feishu.py

async def send_review_notification(
    content_id: str,
    title: str,
    preview: str,
    created_at: str
) -> bool:
    """发送审核通知到飞书"""
```

---

## 4. 定时任务架构

### 4.1 Celery 配置

```python
# app/tasks/celery_app.py

celery_app.conf.beat_schedule = {
    # 抓取已发布内容的数据
    "fetch-published-analytics": {
        "task": "tasks.fetch_analytics",
        "schedule": 3600.0,  # 每小时
    },
    # 热点追踪 - 每2小时抓取（7:00-23:00）
    "fetch-hotspots": {
        "task": "tasks.fetch_hotspots",
        "schedule": 7200.0,  # 2小时
    },
    # 每日热点精选推送
    "send-daily-hotspot-digest": {
        "task": "tasks.send_daily_hotspot_digest",
        "schedule": crontab(hour=22, minute=0),  # 每晚22:00
    },
    # 清理过期热点
    "clean-expired-hotspots": {
        "task": "tasks.clean_expired_hotspots",
        "schedule": crontab(hour=3, minute=0),  # 每天凌晨3:00
    },
    # 刷新小红书账号数据 - 每小时
    "refresh-xhs-account": {
        "task": "tasks.refresh_xhs_account",
        "schedule": 3600.0,  # 每小时
    },
    # Agent 热点抓取 V2 - 每2小时
    "fetch-hotspots-v2": {
        "task": "tasks.fetch_hotspots_v2",
        "schedule": 7200.0,  # 2小时
    },
}
```

### 4.2 定时任务列表

| 任务名称 | 调度规则 | 优先级 | 功能描述 |
|---------|---------|-------|---------|
| fetch_hotspots | 每2小时 (7-23点) | 高 | 抓取全网热点话题 |
| fetch_hotspots_v2 | 每2小时 | 中 | Agent模式热点抓取 |
| refresh_xhs_account | 每小时 | 中 | 刷新小红书账号数据 |
| fetch_analytics | 每小时 | 中 | 抓取已发布内容数据 |
| send_daily_hotspot_digest | 每天22:00 | 中 | 每日热点精选推送 |
| clean_expired_hotspots | 每天03:00 | 低 | 清理过期热点数据 |

---

## 5. 数据模型

### 5.1 ER图 (Mermaid)

```mermaid
erDiagram
    HotTopic ||--o{ Content : "关联"
    HotTopic ||--o{ HotTopicTrend : "趋势记录"
    HotTopic ||--o{ HotTopicAlert : "推送记录"
    Content ||--o{ ContentMetric : "指标数据"
    Content ||--o{ WorkflowLog : "执行日志"
    
    HotTopic {
        string id PK
        string title "标题"
        string summary "摘要"
        int heat_score "热度分"
        int professional_score "专业分"
        int safety_score "安全分"
        int total_score "综合分"
        string trend "趋势 rising/falling"
        string category "分类"
        json keywords "关键词"
        string status "状态"
        string compliance_flag "合规标记"
        datetime discovered_at "发现时间"
        datetime expires_at "过期时间"
    }
    
    Content {
        string id PK
        string workflow_id UK "工作流ID"
        string topic_id FK "热点ID"
        json titles "候选标题(3个)"
        text body "正文"
        json tags "标签"
        json image_prompts "配图提示词"
        json images "生成的图片"
        string status "状态 CREATING/REVIEWING/APPROVED"
        int revision_round "修改轮次"
        datetime approved_at "通过时间"
        datetime published_at "发布时间"
    }
    
    ContentMetric {
        string id PK
        string content_id FK
        int views "阅读量"
        int likes "点赞"
        int comments "评论"
        int favorites "收藏"
        float engagement_rate "互动率"
    }
    
    HotTopicTrend {
        string id PK
        string topic_id FK
        int heat_score "热度分"
        int search_index "搜索指数"
        int discuss_count "讨论量"
        datetime recorded_at "记录时间"
    }
    
    WorkflowLog {
        string id PK
        string workflow_id "工作流ID"
        string agent_name "Agent名称"
        string action "动作"
        json input_data "输入"
        json output_data "输出"
        string status "状态"
        int duration_ms "耗时"
    }
```

### 5.2 核心实体说明

```python
# app/models/v4_models.py

class HotTopic(Base):
    """热点表 - PRD v4.0"""
    # 评分维度: heat_score, professional_score, safety_score, innovation_score, total_score
    # 追踪字段: trend, category, keywords, search_index, discuss_count, read_count
    # 状态管理: compliance_flag, status, is_notified

class Content(Base):
    """内容表"""
    # 创作数据: titles(3个候选), body, tags, image_prompts, images
    # 审核状态: CREATING → REVIEWING → APPROVED → PUBLISHED
    # 修改记录: revision_round, revision_notes, error_message

class ContentMetric(Base):
    """内容表现指标表"""
    # 互动数据: views, likes, comments, favorites, shares
    # 计算指标: engagement_rate
    # 数据来源: data_source (manual/api/demo)
```

---

## 6. API 设计

### 6.1 RESTful API 列表

```
# 内容管理
GET    /api/v1/contents                    # 获取内容列表
GET    /api/v1/contents/{id}               # 获取内容详情
POST   /api/v1/contents/{id}/approve       # 审核通过
POST   /api/v1/contents/{id}/reject        # 拒绝内容
POST   /api/v1/contents/{id}/auto-publish  # 发布内容
POST   /api/v1/contents/{id}/regenerate    # 重新生成

# 热点管理
GET    /api/v1/agent/hotspots/search       # 实时搜索热点
GET    /api/v1/hotspots                    # 获取热点列表
GET    /api/v1/hotspots/{id}               # 获取热点详情

# Workflow
POST   /api/v1/agent/workflow/start        # 启动创作工作流
POST   /api/v1/agent/workflow/batch        # 批量创作
GET    /api/v1/agent/workflow/{id}         # 查询工作流状态

# 定时任务
GET    /api/v1/scheduler/tasks             # 获取定时任务列表
GET    /api/v1/scheduler/status            # 获取调度器状态
GET    /api/v1/scheduler/executions        # 获取执行历史
POST   /api/v1/scheduler/tasks/{id}/run    # 立即执行任务

# 文档
GET    /api/docs                           # Swagger UI
GET    /api/redoc                         # ReDoc
```

### 6.2 WebSocket API

```
WS /ws/{client_id}

# 消息类型
ping/pong          # 心跳检测
review_decision    # 审核决策
workflow_update    # 工作流状态更新
notification       # 系统通知
```

---

## 7. 部署架构

### 7.1 Docker Compose 配置

```yaml
# docker-compose.yml

services:
  # Nginx 网关
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./frontend/dist:/usr/share/nginx/html:ro
    depends_on:
      - api

  # API 服务
  api:
    build: ./backend
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/xhs_platform
      - REDIS_URL=redis://redis:6379/0
      - RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
      - ARK_API_KEY=${ARK_API_KEY}
      - ARK_MODEL_ENDPOINT=${ARK_MODEL_ENDPOINT}
      - ARK_IMAGE_ENDPOINT=${ARK_IMAGE_ENDPOINT}
      - BRAVE_API_KEY=${BRAVE_API_KEY}
      - MCP_URL=http://xiaohongshu-mcp:18060/mcp
    depends_on:
      - postgres
      - redis
      - rabbitmq

  # Celery Worker
  celery-worker:
    build: ./backend
    command: celery -A app.tasks.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/xhs_platform
      - CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672/
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
      - rabbitmq

  # Celery Beat
  celery-beat:
    build: ./backend
    command: celery -A app.tasks.celery_app beat --loglevel=info
    environment:
      - CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672/
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis
      - rabbitmq

  # PostgreSQL
  postgres:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=xhs_platform

  # Redis
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  # RabbitMQ
  rabbitmq:
    image: rabbitmq:3-alpine
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq

  # 小红书 MCP 服务
  xiaohongshu-mcp:
    build: ./mcp
    ports:
      - "18060:18060"
    volumes:
      - ./mcp/cookies.json:/app/cookies.json:ro

volumes:
  postgres_data:
  redis_data:
  rabbitmq_data:
```

### 7.2 Nginx 配置

```nginx
server {
    listen 80;
    
    # 前端静态资源
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    # API 代理到后端
    location /api/ {
        proxy_pass http://api:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # WebSocket 代理
    location /ws/ {
        proxy_pass http://api:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 8. 环境变量配置

```bash
# === 应用配置 ===
APP_NAME=新媒体智能运营平台
DEBUG=True
API_KEY=xhs_agent_internal_key
FRONTEND_URL=http://localhost

# === 数据库配置 ===
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/xhs_platform
REDIS_URL=redis://localhost:6379/0
RABBITMQ_URL=amqp://guest:guest@localhost:5672/

# === 方舟大模型 (文本生成) ===
ARK_API_KEY=${ARK_API_KEY}
ARK_MODEL_ENDPOINT=${ARK_MODEL_ENDPOINT}
ARK_IMAGE_ENDPOINT=${ARK_IMAGE_ENDPOINT}
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3

# === Brave Search (热点搜索) ===
BRAVE_API_KEY=${BRAVE_API_KEY}

# === MCP 服务配置 ===
MCP_URL=http://localhost:18060/mcp
MCP_ENABLED=true

# === 小红书账号配置 ===
XHS_USER_ID=${XHS_USER_ID}
```

---

## 9. 关键业务流程

### 9.1 单次创作流程 (Mermaid)

```mermaid
sequenceDiagram
    autonumber
    
    participant User as 用户
    participant API as API服务
    participant DB as 数据库
    participant Agent as LangGraph
    participant LLM as 方舟大模型
    participant Feishu as 飞书
    
    User->>API: POST /workflow/start
    API->>DB: 创建Content记录<br/>(status=CREATING)
    API->>User: 返回workflow_id
    
    par 异步执行工作流
        API->>Agent: 启动LangGraph工作流
        
        Agent->>Agent: Research Agent<br/>Brave Search搜索热点
        Agent->>Agent: Compliance Agent<br/>合规检查
        Agent->>LLM: Creator Agent<br/>生成文案
        LLM-->>Agent: 返回titles/body/tags
        Agent->>LLM: Image Service<br/>生成配图
        
        Agent->>Feishu: 发送审核通知
        Agent->>DB: 更新Content<br/>(status=REVIEWING)
    end
    
    User->>Feishu: 回复"通过"
    Feishu->>API: 审核回调
    API->>DB: 更新Content<br/>(status=APPROVED)
    API->>Feishu: 回复审核结果
```

### 9.2 定时任务执行流程

```mermaid
sequenceDiagram
    autonumber
    
    participant Beat as Celery Beat
    participant Queue as RabbitMQ队列
    participant Worker as Celery Worker
    participant Agent as Hotspot Agent
    participant Search as Brave Search
    participant DB as PostgreSQL
    participant Feishu as 飞书
    
    Beat->>Beat: 到达调度时间
    Beat->>Queue: 发送任务消息
    
    Worker->>Queue: 获取任务
    Worker->>Agent: 执行fetch_hotspots
    
    Agent->>Search: 搜索财经热点
    Search-->>Agent: 返回热点列表
    
    Agent->>Agent: 分类/评分/去重
    Agent->>DB: 保存HotTopic记录
    
    alt 高热度热点
        Agent->>Feishu: 发送实时推送
    end
```

---

## 10. Docker部署架构

### 10.1 容器架构图 (Mermaid)

```mermaid
graph TB
    subgraph DockerCompose["🐳 Docker Compose 环境"]
        subgraph Network["xhs-network (bridge)"]
            Nginx["🌐 Nginx<br/>Port: 80<br/>Container: xhs_nginx"]
            
            subgraph BackendServices["后端服务"]
                API["⚡ FastAPI<br/>Port: 8000<br/>Container: xhs_api"]
                Worker["🔧 Celery Worker<br/>Container: xhs_worker"]
                Scheduler["⏰ Celery Beat<br/>Container: xhs_scheduler"]
            end
            
            subgraph DataServices["数据服务"]
                Postgres["🐘 PostgreSQL<br/>Port: 5432<br/>Container: xhs_postgres"]
                Redis["🔴 Redis<br/>Port: 6379<br/>Container: xhs_redis"]
                RabbitMQ["🐰 RabbitMQ<br/>Port: 5672<br/>Container: xhs_rabbitmq"]
            end
        end
    end
    
    subgraph External["外部服务"]
        MCP["🔌 MCP Server<br/>Host: host.docker.internal:18060"]
        Brave["🔍 Brave Search API"]
        ArkLLM["🤖 方舟大模型"]
        Feishu["💬 飞书 API"]
    end
    
    User["👤 用户浏览器"] -->|HTTP| Nginx
    Nginx -->|/api/*| API
    Nginx -->|静态资源| Frontend["📁 前端文件"]
    
    API --> Postgres
    API --> Redis
    API --> RabbitMQ
    API -->|HTTP| MCP
    API -->|HTTPS| Brave
    API -->|HTTPS| ArkLLM
    API -->|HTTPS| Feishu
    
    Worker --> Postgres
    Worker --> Redis
    Worker --> RabbitMQ
    
    Scheduler --> RabbitMQ
    
    Worker -.->|异步任务| API
```

### 10.2 服务依赖关系

```mermaid
flowchart TD
    subgraph 启动顺序
        DB["1️⃣ PostgreSQL<br/>Redis<br/>RabbitMQ"] --健康检查通过--> API
        API --> Worker
        API --> Scheduler
        API --> Nginx
    end
    
    style DB fill:#e8f5e9
    style API fill:#e3f2fd
    style Nginx fill:#fff3e0
```

| 服务 | 容器名 | 内部端口 | 外部端口 | 依赖 |
|------|--------|---------|---------|------|
| **Nginx** | xhs_nginx | 80 | 80 | api |
| **API** | xhs_api | 8000 | - | postgres, redis, rabbitmq |
| **Worker** | xhs_worker | - | - | postgres, rabbitmq |
| **Scheduler** | xhs_scheduler | - | - | postgres, rabbitmq |
| **PostgreSQL** | xhs_postgres | 5432 | - | - |
| **Redis** | xhs_redis | 6379 | - | - |
| **RabbitMQ** | xhs_rabbitmq | 5672 | - | - |

---

## 11. 部署说明

### 11.1 生产环境部署

#### 步骤1: 环境准备

```bash
# 系统要求
- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ RAM
- 10GB+ 磁盘空间

# 克隆项目
git clone https://github.com/Jenny-Huijing/openclaw-mop.git
cd xhs_platform
```

#### 步骤2: 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入以下必需配置
nano .env
```

**必需配置项：**

```bash
# === 方舟大模型 (文本生成) ===
ARK_API_KEY=your-ark-api-key
ARK_MODEL_ENDPOINT=ep-xxxxxxxxx    # 豆包文本模型端点
ARK_IMAGE_ENDPOINT=ep-xxxxxxxxx    # 即梦图像模型端点

# === Brave Search (热点搜索) ===
BRAVE_API_KEY=your-brave-api-key

# === MCP 服务配置 ===
MCP_URL=http://host.docker.internal:18060/mcp
MCP_ENABLED=true

# === 小红书账号 ===
XHS_USER_ID=your-xiaohongshu-user-id

# === 前端地址 ===
FRONTEND_URL=http://localhost
```

#### 步骤3: 构建并启动服务

```bash
# 构建镜像并启动所有服务
docker-compose up -d --build

# 查看服务状态
docker-compose ps

# 等待所有服务健康检查通过（约30秒）
docker-compose ps | grep "healthy"
```

#### 步骤4: 验证部署

```bash
# 测试API
curl http://localhost/api/v1/contents?limit=1

# 查看API日志
docker logs -f xhs_api

# 查看定时任务日志
docker logs -f xhs_worker
docker logs -f xhs_scheduler
```

### 11.2 日常运维命令

```bash
# 查看所有服务状态
docker-compose ps

# 查看服务日志
docker logs -f xhs_api              # API服务日志
docker logs -f xhs_worker           # Worker日志
docker logs -f xhs_scheduler        # 定时器日志
docker logs -f xhs_postgres         # 数据库日志

# 重启服务
docker-compose restart api          # 重启API
docker-compose restart worker       # 重启Worker
docker-compose restart              # 重启所有服务

# 停止服务
docker-compose stop                 # 停止（保留容器）
docker-compose down                 # 停止并删除容器
docker-compose down -v              # 停止并删除容器+数据卷（危险！）

# 进入容器调试
docker exec -it xhs_api bash
docker exec -it xhs_postgres psql -U postgres -d xhs_platform

# 查看资源使用
docker stats
```

### 11.3 数据备份与恢复

```bash
# 备份数据库
docker exec xhs_postgres pg_dump -U postgres xhs_platform > backup_$(date +%Y%m%d).sql

# 恢复数据库
docker exec -i xhs_postgres psql -U postgres -d xhs_platform < backup_20260214.sql

# 备份数据卷
docker run --rm -v xhs_platform_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .
```

### 11.4 更新部署

```bash
# 拉取最新代码
git pull origin main

# 重新构建并重启
docker-compose up -d --build

# 仅更新代码（开发模式）
docker-compose restart api worker scheduler
```

---

## 12. 本地开发启动

```bash
# 1. 启动基础设施
docker-compose up -d postgres redis rabbitmq

# 2. 安装后端依赖
cd backend
pip install -r requirements.txt

# 3. 启动API服务
uvicorn app.main:app --reload --port 8000

# 4. 启动Celery Worker (新终端)
celery -A app.tasks.celery_app worker --loglevel=info

# 5. 启动Celery Beat (新终端)
celery -A app.tasks.celery_app beat --loglevel=info

# 6. 启动前端 (新终端)
cd frontend
npm install
npm run dev
```

---

## 13. 架构演进记录

| 日期 | 版本 | 变更内容 |
|------|------|----------|
| 2026-02-14 | v2.2 | 统一Docker部署，所有服务容器化 |
| 2026-02-14 | v2.2 | 更新Nginx配置，支持Docker内部网络 |
| 2026-02-14 | v2.2 | 添加详细部署文档和运维命令 |
| 2026-02-14 | v2.1 | 添加Celery定时任务系统，修复配置问题 |
| 2026-02-14 | v2.1 | 添加MCP服务集成，支持小红书账号数据获取 |
| 2026-02-14 | v2.1 | 添加飞书服务，实现审核通知推送 |
| 2026-02-14 | v2.1 | 添加FRONTEND_URL配置字段 |
| 2026-02-12 | v2.0 | 引入 LangGraph 工作流编排，实现多Agent协作 |
| 2026-02-12 | v2.0 | 接入 Brave Search API 实时热点搜索 |
| 2026-02-12 | v2.0 | 接入方舟大模型 (豆包) 内容生成 |
| 2026-02-12 | v2.0 | 接入即梦模型配图生成 |
| 2026-02-10 | v1.0 | 初始版本，基础CRUD功能 |

---

## 13. 项目目录结构

```
xhs_platform/
├── README.md                 # 项目说明
├── ARCHITECTURE.md          # 架构文档 (本文档)
├── docker-compose.yml       # Docker编排
├── .env.example            # 环境变量模板
│
├── backend/                # 后端服务
│   ├── app/
│   │   ├── agents/        # AI Agent实现
│   │   │   ├── orchestrator.py      # 工作流总调度
│   │   │   └── hotspot_agent.py     # 热点获取Agent
│   │   ├── api/           # API路由
│   │   │   └── v1/
│   │   │       ├── agent.py         # Agent API
│   │   │       ├── content.py       # 内容API
│   │   │       ├── scheduler.py     # 定时任务API
│   │   │       └── ...
│   │   ├── core/          # 核心配置
│   │   │   ├── config.py            # 应用配置
│   │   │   └── database.py          # 数据库配置
│   │   ├── models/        # 数据模型
│   │   │   └── v4_models.py         # PRD v4.0模型
│   │   ├── services/      # 业务服务
│   │   │   ├── llm.py              # LLM服务
│   │   │   ├── search.py           # 搜索服务
│   │   │   ├── image.py            # 图片服务
│   │   │   ├── feishu.py           # 飞书服务
│   │   │   └── xhs_mcp.py          # MCP服务
│   │   └── tasks/         # 定时任务
│   │       ├── celery_app.py       # Celery配置
│   │       ├── content_tasks.py    # 内容任务
│   │       └── hotspot_tasks.py    # 热点任务
│   ├── requirements.txt    # Python依赖
│   └── Dockerfile         # 后端镜像
│
├── frontend/              # 前端应用
│   ├── src/
│   │   ├── components/    # 组件
│   │   ├── views/         # 页面
│   │   ├── composables/   # 组合式函数
│   │   └── utils/         # 工具函数
│   ├── package.json
│   └── Dockerfile
│
├── mcp/                   # 小红书MCP服务
│   ├── mcp_server.py
│   ├── xiaohongshu.py
│   └── Dockerfile
│
├── nginx/                 # Nginx配置
│   └── nginx.conf
│
├── docs/                  # 文档
│   ├── content_status_design.md
│   └── database_migration_20260213.md
│
└── scripts/              # 脚本工具
    └── notify_processor.py
```

---

**文档维护**: 每次架构变更后更新此文档  
**最后更新**: 2026-02-14  
**维护人**: 小珑宝 🤖  
**GitHub**: https://github.com/Jenny-Huijing/openclaw-mop

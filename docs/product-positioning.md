# 产品定位 - 新媒体智能运营平台

## 产品名称
**新媒体智能运营平台** (AI Content Creation Platform)

## 一句话定位
AI驱动的内容创作平台，通过LangGraph多Agent协作，实现从热点发现、智能创作到人工审核的全流程自动化，让内容运营效率提升10倍。

## 核心功能

### 1. 工作台 Dashboard
- **数据统计卡片**: 今日生成/创作中/待确认/累计确认
- **内容列表**: 按状态筛选（全部/创作中/待审核/已通过/已发布）
- **异步创作**: 点击"开始创作"后立即返回，后台AI生成内容

### 2. AI内容创作 Workflow
- **LangGraph Agent架构**:
  - Research Agent: 发现热点话题
  - Compliance Agent: 合规检查
  - Creator Agent: 调用LLM生成文案 + 图像生成
  - Publisher Agent: 发布管理
- **输出内容**:
  - 3个候选标题
  - 正文内容（带emoji、分点说明）
  - 标签数组
  - AI生成配图（2张）

### 3. 内容管理
- 状态流转: CREATING → reviewing → approved → published
- 一键复制: 复制标题+正文+标签到剪贴板
- 人工审核: 通过/拒绝操作

### 4. 实时反馈
- Toast通知: 创作启动/完成提示
- 轮询更新: 自动刷新内容状态
- 进度展示: 按钮显示"AI生成中..."

## 技术亮点

| 特性 | 实现 |
|------|------|
| **Agent架构** | LangGraph状态图编排 |
| **大模型** | 方舟 DeepSeek-V3 |
| **图像生成** | 方舟 Seedream-3.0 |
| **前端框架** | Vue 3 + TypeScript + Tailwind CSS |
| **后端框架** | FastAPI + SQLAlchemy 2.0 |
| **部署方式** | Docker Compose |

## 目标用户

- 银行/金融行业内容运营者
- 个人自媒体创作者
- 企业新媒体运营团队

## 当前实现状态

### 已完成功能 ✅
- LangGraph 5-Agent协作架构
- 方舟大模型文案生成
- Seedream AI图像生成
- 异步创作Workflow
- 内容审核流程
- 模块化前端架构
- Docker Compose部署

### 待实现功能 📋
- 热点自动发现（定时任务）
- WebSocket实时推送
- 多平台发布（小红书API、微信公众号）
- 数据分析看板
- 用户权限管理

## 设计风格

- **极简主义**: 大量留白，信息层级清晰
- **配色方案**: 
  - 主色: 蓝色系 (#3B82F6)
  - 成功: 绿色 (#10B981)
  - 警告: 琥珀色 (#F59E0B)
  - 背景: slate-50
- **组件风格**: Tailwind CSS, Heroicons

## 使用流程

```
1. 用户访问 http://localhost
2. 点击"开始创作"按钮
3. 系统后台执行Workflow（约30-40秒）
4. 列表显示"创作中"状态
5. 创作完成，状态变为"待审核"
6. 点击查看详情，复制内容发布到小红书
```

## 配置要求

**最低配置**:
- Docker Desktop
- 4GB 内存
- 方舟API Key

**推荐配置**:
- Docker Desktop
- 8GB 内存
- 方舟API Key + 图像生成接入点

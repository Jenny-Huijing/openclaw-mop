-- 新媒体智能运营平台 - SQLite 数据库初始化脚本
-- 适用于开发环境
-- 创建日期: 2026-02-12

-- 启用外键支持
PRAGMA foreign_keys = ON;

-- ============================================
-- 1. 用户表 (user_preferences)
-- ============================================
CREATE TABLE IF NOT EXISTS user_preferences (
    id TEXT PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL,
    persona_config TEXT DEFAULT '{}',
    content_style TEXT DEFAULT '{}',
    review_rules TEXT DEFAULT '{}',
    notification_config TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 2. 热点表 (hot_topics)
-- ============================================
CREATE TABLE IF NOT EXISTS hot_topics (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    summary TEXT,
    category TEXT,
    
    -- 评分维度
    heat_score INTEGER CHECK (heat_score BETWEEN 0 AND 100),
    professional_score INTEGER CHECK (professional_score BETWEEN 0 AND 100),
    safety_score INTEGER CHECK (safety_score BETWEEN 0 AND 100),
    innovation_score INTEGER CHECK (innovation_score BETWEEN 0 AND 100),
    total_score INTEGER CHECK (total_score BETWEEN 0 AND 100),
    
    -- 来源信息
    source TEXT,
    source_url TEXT,
    source_urls TEXT DEFAULT '[]',
    
    -- AI分析
    angle TEXT,
    analyzed_at TIMESTAMP,
    
    -- 关联
    created_task_id TEXT,
    
    -- 状态
    compliance_flag TEXT DEFAULT 'PASS',
    status TEXT DEFAULT 'DISCOVERED',
    
    -- 时间戳
    discovered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 热点表索引
CREATE INDEX IF NOT EXISTS idx_hot_topics_status_score ON hot_topics(status, total_score DESC);
CREATE INDEX IF NOT EXISTS idx_hot_topics_category ON hot_topics(category);
CREATE INDEX IF NOT EXISTS idx_hot_topics_created_at ON hot_topics(created_at DESC);

-- ============================================
-- 3. 内容表 (contents)
-- ============================================
CREATE TABLE IF NOT EXISTS contents (
    id TEXT PRIMARY KEY,
    workflow_id TEXT UNIQUE NOT NULL,
    topic_id TEXT REFERENCES hot_topics(id) ON DELETE SET NULL,
    
    -- 内容字段
    titles TEXT DEFAULT '[]',
    body TEXT,
    tags TEXT DEFAULT '[]',
    
    -- AI生成字段
    image_prompts TEXT DEFAULT '[]',
    images TEXT DEFAULT '[]',
    
    -- 合规检查
    compliance_result TEXT,
    quality_report TEXT,
    
    -- 状态
    status TEXT DEFAULT 'CREATING',
    
    -- 修改记录
    revision_round INTEGER DEFAULT 0,
    revision_notes TEXT,
    
    -- 发布信息
    approved_at TIMESTAMP,
    published_at TIMESTAMP,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 内容表索引
CREATE INDEX IF NOT EXISTS idx_contents_status_updated ON contents(status, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_contents_workflow ON contents(workflow_id);
CREATE INDEX IF NOT EXISTS idx_contents_topic ON contents(topic_id);
CREATE INDEX IF NOT EXISTS idx_contents_created_at ON contents(created_at DESC);

-- ============================================
-- 4. 内容指标表 (content_metrics)
-- ============================================
CREATE TABLE IF NOT EXISTS content_metrics (
    id TEXT PRIMARY KEY,
    content_id TEXT NOT NULL REFERENCES contents(id) ON DELETE CASCADE,
    
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    favorites INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    
    engagement_rate REAL,
    data_source TEXT DEFAULT 'manual',
    
    tracked_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_metrics_content_tracked ON content_metrics(content_id, tracked_at DESC);

-- ============================================
-- 5. 工作流日志表 (workflow_logs)
-- ============================================
CREATE TABLE IF NOT EXISTS workflow_logs (
    id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    agent_name TEXT,
    action TEXT,
    
    input_data TEXT,
    output_data TEXT,
    llm_calls TEXT,
    
    status TEXT DEFAULT 'PENDING',
    error_message TEXT,
    duration_ms INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_logs_workflow_time ON workflow_logs(workflow_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_logs_agent ON workflow_logs(agent_name);
CREATE INDEX IF NOT EXISTS idx_logs_status ON workflow_logs(status);

-- ============================================
-- 6. WebSocket连接表 (ws_connections)
-- ============================================
CREATE TABLE IF NOT EXISTS ws_connections (
    id TEXT PRIMARY KEY,
    client_id TEXT UNIQUE NOT NULL,
    connection_status TEXT DEFAULT 'DISCONNECTED',
    last_heartbeat TIMESTAMP,
    connected_at TIMESTAMP,
    disconnected_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 7. 消息投递记录表 (message_deliveries)
-- ============================================
CREATE TABLE IF NOT EXISTS message_deliveries (
    id TEXT PRIMARY KEY,
    msg_id TEXT UNIQUE NOT NULL,
    workflow_id TEXT,
    event_type TEXT,
    payload TEXT,
    status TEXT DEFAULT 'PENDING',
    retry_count INTEGER DEFAULT 0,
    sent_at TIMESTAMP,
    acked_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_messages_msg_status ON message_deliveries(msg_id, status);
CREATE INDEX IF NOT EXISTS idx_messages_workflow ON message_deliveries(workflow_id);

-- ============================================
-- 8. 更新时间触发器 (SQLite版本)
-- ============================================
CREATE TRIGGER IF NOT EXISTS update_user_preferences_updated_at
AFTER UPDATE ON user_preferences
BEGIN
    UPDATE user_preferences SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_hot_topics_updated_at
AFTER UPDATE ON hot_topics
BEGIN
    UPDATE hot_topics SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_contents_updated_at
AFTER UPDATE ON contents
BEGIN
    UPDATE contents SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- 验证表创建
SELECT 'Tables created:' as info, COUNT(*) as count FROM sqlite_master WHERE type='table' AND name IN ('user_preferences', 'hot_topics', 'contents', 'content_metrics', 'workflow_logs', 'ws_connections', 'message_deliveries');

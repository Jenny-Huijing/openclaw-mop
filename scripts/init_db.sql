-- 新媒体智能运营平台 - 数据库初始化脚本
-- 支持: PostgreSQL 15+
-- 创建日期: 2026-02-12

-- 启用 UUID 扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- 1. 用户表 (user_preferences)
-- ============================================
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(100) UNIQUE NOT NULL,
    persona_config JSONB DEFAULT '{}',
    content_style JSONB DEFAULT '{}',
    review_rules JSONB DEFAULT '{}',
    notification_config JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE user_preferences IS '用户配置表';
COMMENT ON COLUMN user_preferences.user_id IS '用户唯一标识';

-- ============================================
-- 2. 热点表 (hot_topics)
-- ============================================
CREATE TABLE IF NOT EXISTS hot_topics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    summary TEXT,
    category VARCHAR(50),
    
    -- 评分维度
    heat_score INTEGER CHECK (heat_score BETWEEN 0 AND 100),
    professional_score INTEGER CHECK (professional_score BETWEEN 0 AND 100),
    safety_score INTEGER CHECK (safety_score BETWEEN 0 AND 100),
    innovation_score INTEGER CHECK (innovation_score BETWEEN 0 AND 100),
    total_score INTEGER CHECK (total_score BETWEEN 0 AND 100),
    
    -- 来源信息
    source VARCHAR(100),
    source_url TEXT,
    source_urls JSONB DEFAULT '[]',
    
    -- AI分析
    angle TEXT,
    analyzed_at TIMESTAMP WITH TIME ZONE,
    
    -- 关联
    created_task_id UUID,
    
    -- 状态
    compliance_flag VARCHAR(20) DEFAULT 'PASS',
    status VARCHAR(20) DEFAULT 'DISCOVERED',
    
    -- 时间戳
    discovered_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE hot_topics IS '热点表 - 实时财经热点';
COMMENT ON COLUMN hot_topics.heat_score IS '热度分 0-100';
COMMENT ON COLUMN hot_topics.professional_score IS '专业匹配度 0-100';
COMMENT ON COLUMN hot_topics.compliance_flag IS 'PASS/WARNING/BLOCK';

-- 热点表索引
CREATE INDEX IF NOT EXISTS idx_hot_topics_status_score ON hot_topics(status, total_score DESC);
CREATE INDEX IF NOT EXISTS idx_hot_topics_category ON hot_topics(category);
CREATE INDEX IF NOT EXISTS idx_hot_topics_created_at ON hot_topics(created_at DESC);

-- ============================================
-- 3. 内容表 (contents)
-- ============================================
CREATE TABLE IF NOT EXISTS contents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id VARCHAR(100) UNIQUE NOT NULL,
    topic_id UUID REFERENCES hot_topics(id) ON DELETE SET NULL,
    
    -- 内容字段
    titles JSONB DEFAULT '[]',
    body TEXT,
    tags JSONB DEFAULT '[]',
    
    -- AI生成字段
    image_prompts JSONB DEFAULT '[]',
    images JSONB DEFAULT '[]',
    
    -- 合规检查
    compliance_result JSONB,
    quality_report JSONB,
    
    -- 状态
    status VARCHAR(20) DEFAULT 'CREATING',
    -- CREATING/REVIEWING/APPROVED/REJECTED/PUBLISHED
    
    -- 修改记录
    revision_round INTEGER DEFAULT 0,
    revision_notes TEXT,
    
    -- 发布信息
    approved_at TIMESTAMP WITH TIME ZONE,
    published_at TIMESTAMP WITH TIME ZONE,
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE contents IS '内容表 - AI生成的笔记内容';
COMMENT ON COLUMN contents.workflow_id IS 'LangGraph工作流ID';
COMMENT ON COLUMN contents.status IS 'CREATING/REVIEWING/APPROVED/REJECTED/PUBLISHED';

-- 内容表索引
CREATE INDEX IF NOT EXISTS idx_contents_status_updated ON contents(status, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_contents_workflow ON contents(workflow_id);
CREATE INDEX IF NOT EXISTS idx_contents_topic ON contents(topic_id);
CREATE INDEX IF NOT EXISTS idx_contents_created_at ON contents(created_at DESC);

-- ============================================
-- 4. 内容指标表 (content_metrics)
-- ============================================
CREATE TABLE IF NOT EXISTS content_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_id UUID NOT NULL REFERENCES contents(id) ON DELETE CASCADE,
    
    -- 互动数据
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    favorites INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    
    -- 计算指标
    engagement_rate FLOAT,
    
    -- 数据来源
    data_source VARCHAR(20) DEFAULT 'manual',
    
    -- 时间戳
    tracked_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE content_metrics IS '内容表现指标表';

-- 指标表索引
CREATE INDEX IF NOT EXISTS idx_metrics_content_tracked ON content_metrics(content_id, tracked_at DESC);

-- ============================================
-- 5. 工作流日志表 (workflow_logs)
-- ============================================
CREATE TABLE IF NOT EXISTS workflow_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id VARCHAR(100) NOT NULL,
    agent_name VARCHAR(100),
    action VARCHAR(100),
    
    -- 数据记录
    input_data JSONB,
    output_data JSONB,
    llm_calls JSONB,
    
    -- 执行状态
    status VARCHAR(20) DEFAULT 'PENDING',
    -- SUCCESS/FAILED/PENDING
    
    error_message TEXT,
    duration_ms INTEGER,
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE workflow_logs IS 'Workflow执行日志表';
COMMENT ON COLUMN workflow_logs.agent_name IS '执行的Agent名称';

-- 日志表索引
CREATE INDEX IF NOT EXISTS idx_logs_workflow_time ON workflow_logs(workflow_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_logs_agent ON workflow_logs(agent_name);
CREATE INDEX IF NOT EXISTS idx_logs_status ON workflow_logs(status);

-- ============================================
-- 6. WebSocket连接表 (ws_connections)
-- ============================================
CREATE TABLE IF NOT EXISTS ws_connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id VARCHAR(100) UNIQUE NOT NULL,
    
    connection_status VARCHAR(20) DEFAULT 'DISCONNECTED',
    -- CONNECTED/DISCONNECTED
    
    last_heartbeat TIMESTAMP WITH TIME ZONE,
    connected_at TIMESTAMP WITH TIME ZONE,
    disconnected_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE ws_connections IS 'WebSocket连接管理表';

-- ============================================
-- 7. 消息投递记录表 (message_deliveries)
-- ============================================
CREATE TABLE IF NOT EXISTS message_deliveries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    msg_id VARCHAR(100) UNIQUE NOT NULL,
    workflow_id VARCHAR(100),
    event_type VARCHAR(100),
    payload JSONB,
    
    status VARCHAR(20) DEFAULT 'PENDING',
    -- PENDING/SENT/ACKED/FAILED
    
    retry_count INTEGER DEFAULT 0,
    
    sent_at TIMESTAMP WITH TIME ZONE,
    acked_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE message_deliveries IS '消息投递记录表 - 用于追踪和去重';

-- 消息表索引
CREATE INDEX IF NOT EXISTS idx_messages_msg_status ON message_deliveries(msg_id, status);
CREATE INDEX IF NOT EXISTS idx_messages_workflow ON message_deliveries(workflow_id);

-- ============================================
-- 8. 创建更新时间触发器
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为用户表添加触发器
DROP TRIGGER IF EXISTS update_user_preferences_updated_at ON user_preferences;
CREATE TRIGGER update_user_preferences_updated_at
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 为热点表添加触发器
DROP TRIGGER IF EXISTS update_hot_topics_updated_at ON hot_topics;
CREATE TRIGGER update_hot_topics_updated_at
    BEFORE UPDATE ON hot_topics
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 为内容表添加触发器
DROP TRIGGER IF EXISTS update_contents_updated_at ON contents;
CREATE TRIGGER update_contents_updated_at
    BEFORE UPDATE ON contents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 初始化完成
-- ============================================

-- 验证表创建
SELECT 
    'Tables created:' as info,
    COUNT(*) as count
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('user_preferences', 'hot_topics', 'contents', 'content_metrics', 'workflow_logs', 'ws_connections', 'message_deliveries');

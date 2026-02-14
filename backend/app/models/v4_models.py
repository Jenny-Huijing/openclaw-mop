"""
数据库模型 - PRD v4.0 版本
包含7个核心表：热点、内容、指标、日志、配置、连接、消息
"""

from datetime import datetime
from typing import Any, Optional
from sqlalchemy import DateTime, func, String, Text, Integer, Float, JSON, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid

# 使用统一的 Base
from app.models.base import Base


class HotTopic(Base):
    """热点表"""
    __tablename__ = "hot_topics"
    
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    
    # 评分维度
    heat_score: Mapped[Optional[int]] = mapped_column(Integer, default=0)           # 热度分 0-100
    professional_score: Mapped[Optional[int]] = mapped_column(Integer)   # 专业匹配度 0-100
    safety_score: Mapped[Optional[int]] = mapped_column(Integer)         # 安全度 0-100
    innovation_score: Mapped[Optional[int]] = mapped_column(Integer)     # 创新度 0-100
    total_score: Mapped[Optional[int]] = mapped_column(Integer)          # 综合分 0-100
    
    # 新增字段 - 热点追踪系统
    trend: Mapped[Optional[str]] = mapped_column(String(20), default="stable")      # rising/falling/stable
    category: Mapped[Optional[str]] = mapped_column(String(50), default="other")    # 分类
    keywords: Mapped[Optional[list]] = mapped_column(JSON, default=list)            # 关键词
    search_index: Mapped[Optional[int]] = mapped_column(Integer, default=0)         # 搜索指数
    discuss_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)        # 讨论量
    read_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)           # 阅读量
    
    source: Mapped[Optional[str]] = mapped_column(String(100))           # 来源平台
    source_url: Mapped[Optional[str]] = mapped_column(Text)
    related_keywords: Mapped[Optional[list]] = mapped_column(JSON)       # 关联关键词数组
    
    # 状态
    compliance_flag: Mapped[str] = mapped_column(String(20), default="PASS")  # PASS/WARNING/BLOCK
    status: Mapped[str] = mapped_column(String(20), default="DISCOVERED")     # DISCOVERED/SELECTED/ARCHIVED/active/expired/used
    is_notified: Mapped[bool] = mapped_column(default=False)              # 是否已推送
    
    # 时间
    discovered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=func.now())
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)      # 过期时间
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    contents: Mapped[list["Content"]] = relationship("Content", back_populates="topic")
    
    __table_args__ = (
        Index('idx_hot_topics_status_score', 'status', 'total_score'),
        Index('idx_hot_topics_category', 'category', 'status'),
        Index('idx_hot_topics_discovered', 'discovered_at'),
    )
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "heat_score": self.heat_score,
            "professional_score": self.professional_score,
            "safety_score": self.safety_score,
            "innovation_score": self.innovation_score,
            "total_score": self.total_score,
            "category": self.category,
            "trend": self.trend,
            "keywords": self.keywords,
            "search_index": self.search_index,
            "discuss_count": self.discuss_count,
            "read_count": self.read_count,
            "source": self.source,
            "source_url": self.source_url,
            "related_keywords": self.related_keywords,
            "compliance_flag": self.compliance_flag,
            "status": self.status,
            "is_notified": self.is_notified,
            "discovered_at": self.discovered_at.isoformat() if self.discovered_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Content(Base):
    """内容表"""
    __tablename__ = "contents"
    
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    topic_id: Mapped[Optional[str]] = mapped_column(ForeignKey("hot_topics.id"))
    
    titles: Mapped[Optional[list]] = mapped_column(JSON)               # 3个候选标题
    body: Mapped[Optional[str]] = mapped_column(Text)                   # 正文
    tags: Mapped[Optional[list]] = mapped_column(JSON)                 # 标签数组
    image_prompts: Mapped[Optional[list]] = mapped_column(JSON)        # 配图提示词
    images: Mapped[Optional[list]] = mapped_column(JSON)               # 生成的配图 [{url, prompt, status}]
    
    compliance_result: Mapped[Optional[dict]] = mapped_column(JSON)    # 合规审查结果
    quality_report: Mapped[Optional[dict]] = mapped_column(JSON)       # 质量报告
    
    status: Mapped[str] = mapped_column(String(20), default="CREATING")  # CREATING/REVIEWING/APPROVED/REJECTED/PUBLISHED/PUBLISH_FAILED
    revision_round: Mapped[int] = mapped_column(Integer, default=0)     # 修改轮次
    revision_notes: Mapped[Optional[str]] = mapped_column(Text)         # 修改意见
    error_message: Mapped[Optional[str]] = mapped_column(Text)          # 错误/失败原因
    
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    topic: Mapped[Optional["HotTopic"]] = relationship("HotTopic", back_populates="contents")
    metrics: Mapped[list["ContentMetric"]] = relationship("ContentMetric", back_populates="content")
    
    __table_args__ = (
        Index('idx_contents_status_updated', 'status', 'updated_at'),
        Index('idx_contents_workflow', 'workflow_id'),
    )
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "topic_id": self.topic_id,
            "titles": self.titles,
            "body": self.body,
            "tags": self.tags,
            "image_prompts": self.image_prompts,
            "images": self.images,
            "compliance_result": self.compliance_result,
            "quality_report": self.quality_report,
            "status": self.status,
            "revision_round": self.revision_round,
            "revision_notes": self.revision_notes,
            "error_message": self.error_message,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ContentMetric(Base):
    """内容表现指标表"""
    __tablename__ = "content_metrics"
    
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    content_id: Mapped[str] = mapped_column(ForeignKey("contents.id"))
    
    views: Mapped[int] = mapped_column(Integer, default=0)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    favorites: Mapped[int] = mapped_column(Integer, default=0)
    shares: Mapped[int] = mapped_column(Integer, default=0)
    engagement_rate: Mapped[Optional[float]] = mapped_column(Float)     # 互动率
    
    data_source: Mapped[str] = mapped_column(String(20), default="manual")  # manual/api/demo
    tracked_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    # 关系
    content: Mapped["Content"] = relationship("Content", back_populates="metrics")
    
    __table_args__ = (
        Index('idx_metrics_content_tracked', 'content_id', 'tracked_at'),
    )
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "content_id": self.content_id,
            "views": self.views,
            "likes": self.likes,
            "comments": self.comments,
            "favorites": self.favorites,
            "shares": self.shares,
            "engagement_rate": self.engagement_rate,
            "data_source": self.data_source,
            "tracked_at": self.tracked_at.isoformat() if self.tracked_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class WorkflowLog(Base):
    """Workflow 执行日志表"""
    __tablename__ = "workflow_logs"
    
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id: Mapped[str] = mapped_column(String(100), nullable=False)
    agent_name: Mapped[str] = mapped_column(String(100))                 # 哪个 Agent
    action: Mapped[str] = mapped_column(String(100))                     # 执行的动作
    
    input_data: Mapped[Optional[dict]] = mapped_column(JSON)            # 输入数据
    output_data: Mapped[Optional[dict]] = mapped_column(JSON)           # 输出数据
    llm_calls: Mapped[Optional[list]] = mapped_column(JSON)             # LLM 调用记录
    
    status: Mapped[str] = mapped_column(String(20), default="PENDING")   # SUCCESS/FAILED/PENDING
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)          # 执行耗时
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_logs_workflow_time', 'workflow_id', 'created_at'),
    )
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "agent_name": self.agent_name,
            "action": self.action,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "status": self.status,
            "error_message": self.error_message,
            "duration_ms": self.duration_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class UserPreference(Base):
    """用户配置表"""
    __tablename__ = "user_preferences"
    
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    
    persona_config: Mapped[Optional[dict]] = mapped_column(JSON)        # 人设配置
    content_style: Mapped[Optional[dict]] = mapped_column(JSON)         # 内容风格偏好
    review_rules: Mapped[Optional[dict]] = mapped_column(JSON)          # 审核规则
    notification_config: Mapped[Optional[dict]] = mapped_column(JSON)   # 通知配置
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "persona_config": self.persona_config,
            "content_style": self.content_style,
            "review_rules": self.review_rules,
            "notification_config": self.notification_config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class WSConnection(Base):
    """WebSocket 连接管理表"""
    __tablename__ = "ws_connections"
    
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)  # openclaw-gateway
    
    connection_status: Mapped[str] = mapped_column(String(20), default="DISCONNECTED")  # CONNECTED/DISCONNECTED
    last_heartbeat: Mapped[Optional[datetime]] = mapped_column(DateTime)
    connected_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    disconnected_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "client_id": self.client_id,
            "connection_status": self.connection_status,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "connected_at": self.connected_at.isoformat() if self.connected_at else None,
            "disconnected_at": self.disconnected_at.isoformat() if self.disconnected_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class MessageDelivery(Base):
    """消息投递记录表（用于追踪和去重）"""
    __tablename__ = "message_deliveries"
    
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    msg_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    workflow_id: Mapped[Optional[str]] = mapped_column(String(100))
    event_type: Mapped[str] = mapped_column(String(100))                 # 事件类型
    payload: Mapped[Optional[dict]] = mapped_column(JSON)               # 消息内容
    
    status: Mapped[str] = mapped_column(String(20), default="PENDING")   # PENDING/SENT/ACKED/FAILED
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    acked_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_messages_msg_status', 'msg_id', 'status'),
        Index('idx_messages_workflow', 'workflow_id'),
    )
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "msg_id": self.msg_id,
            "workflow_id": self.workflow_id,
            "event_type": self.event_type,
            "payload": self.payload,
            "status": self.status,
            "retry_count": self.retry_count,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "acked_at": self.acked_at.isoformat() if self.acked_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class HotTopicTrend(Base):
    """热点热度趋势记录表"""
    __tablename__ = "hot_topic_trends"
    
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    topic_id: Mapped[str] = mapped_column(String(36), ForeignKey("hot_topics.id"), index=True)
    heat_score: Mapped[int] = mapped_column(Integer, default=0)
    search_index: Mapped[int] = mapped_column(Integer, default=0)
    discuss_count: Mapped[int] = mapped_column(Integer, default=0)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)
    
    __table_args__ = (
        Index('idx_trends_topic_time', 'topic_id', 'recorded_at'),
    )
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "topic_id": self.topic_id,
            "heat_score": self.heat_score,
            "search_index": self.search_index,
            "discuss_count": self.discuss_count,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
        }


class HotTopicAlert(Base):
    """热点推送记录表"""
    __tablename__ = "hot_topic_alerts"
    
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    topic_id: Mapped[str] = mapped_column(String(36), ForeignKey("hot_topics.id"), index=True)
    alert_type: Mapped[str] = mapped_column(String(20))  # new/heat_rise/daily_digest/remind
    heat_score_at_send: Mapped[int] = mapped_column(Integer, default=0)
    feishu_msg_id: Mapped[Optional[str]] = mapped_column(String(100))
    is_read: Mapped[bool] = mapped_column(default=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_alerts_topic_type', 'topic_id', 'alert_type'),
        Index('idx_alerts_sent', 'sent_at'),
    )
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "topic_id": self.topic_id,
            "alert_type": self.alert_type,
            "heat_score_at_send": self.heat_score_at_send,
            "feishu_msg_id": self.feishu_msg_id,
            "is_read": self.is_read,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
        }

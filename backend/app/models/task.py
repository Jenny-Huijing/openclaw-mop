"""
任务模型（旧版，兼容期）
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, JSON, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Task(Base):
    """任务表"""
    __tablename__ = "tasks"
    
    # 任务类型
    type: Mapped[str] = mapped_column(String(50))  # hotspot_analysis, content_creation, publish
    
    # 任务状态
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, doing, review, ready, published, failed, cancelled
    
    # 优先级
    priority: Mapped[str] = mapped_column(String(10), default="medium")  # low, medium, high, urgent
    
    # 时间安排
    scheduled_at: Mapped[Optional[datetime]]
    started_at: Mapped[Optional[datetime]]
    completed_at: Mapped[Optional[datetime]]
    
    # 任务内容
    title: Mapped[str] = mapped_column(String(200))
    topic: Mapped[Optional[str]] = mapped_column(String(50))
    
    # 数据
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    result: Mapped[Optional[dict]] = mapped_column(JSON)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # 统计
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # 来源
    source: Mapped[Optional[str]] = mapped_column(String(50))  # manual, auto_cron, ai_agent

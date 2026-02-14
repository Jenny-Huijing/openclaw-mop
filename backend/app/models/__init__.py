"""
数据库模型 - PRD v4.0
"""

# 基础
from app.models.base import Base

# 任务模型（保留，Celery 仍在使用）
from app.models.task import Task

# 新模型（PRD v4.0）
from app.models.v4_models import (
    HotTopic,
    HotTopicTrend,
    HotTopicAlert,
    Content,
    ContentMetric,
    WorkflowLog,
    UserPreference,
    WSConnection,
    MessageDelivery,
)

__all__ = [
    "Base",
    # 任务（保留）
    "Task",
    # 新模型（v4.0）
    "HotTopic",
    "HotTopicTrend",
    "HotTopicAlert",
    "Content",
    "ContentMetric",
    "WorkflowLog",
    "UserPreference",
    "WSConnection",
    "MessageDelivery",
]

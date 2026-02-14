"""
任务模块
"""

from app.tasks.celery_app import celery_app
from app.tasks.content_tasks import generate_content, publish_content, fetch_analytics

__all__ = ["celery_app", "generate_content", "publish_content", "fetch_analytics"]

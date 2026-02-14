"""
Celery应用配置
"""

from celery import Celery
from celery.schedules import crontab
from celery.signals import task_prerun
from app.core.config import settings
import redis
import json

# 创建Celery应用
celery_app = Celery(
    "nmop",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.content_tasks", "app.tasks.hotspot_tasks", "app.agents.hotspot_agent"]
)

# 配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30分钟超时
    worker_prefetch_multiplier=1,
    # 启用任务事件发送，用于监控
    task_send_sent_event=True,
    worker_send_task_events=True,
)

# 任务名称映射（用于执行记录显示）
TASK_NAME_MAP = {
    "app.tasks.content_tasks.fetch_analytics": "抓取已发布内容数据",
    "app.tasks.hotspot_tasks.fetch_hotspots": "热点追踪抓取",
    "app.tasks.hotspot_tasks.send_daily_hotspot_digest": "每日热点精选推送",
    "app.tasks.hotspot_tasks.clean_expired_hotspots": "清理过期热点",
    "app.tasks.content_tasks.refresh_xhs_account": "刷新小红书账号数据",
    "app.agents.hotspot_agent.fetch_hotspots_v2_task": "Agent热点抓取V2",
    "app.agents.hotspot_agent.fetch_hotspots_custom_task": "自定义热点抓取",
    "tasks.refresh_xhs_account": "刷新小红书账号数据",
    "tasks.fetch_hotspots": "热点追踪抓取",
    "tasks.send_daily_hotspot_digest": "每日热点精选推送",
    "tasks.clean_expired_hotspots": "清理过期热点",
    "tasks.fetch_hotspots_v2": "Agent热点抓取V2",
    "tasks.fetch_hotspots_custom": "自定义热点抓取",
}


@task_prerun.connect
def task_prerun_handler(task_id, task, args, kwargs, **extras):
    """
    任务执行前记录任务名称映射到 Redis
    这样查询执行记录时可以准确显示任务名称
    """
    try:
        r = redis.from_url(settings.CELERY_RESULT_BACKEND)
        task_name = TASK_NAME_MAP.get(task.name, task.name)
        # 保存任务ID和名称的映射，保留7天
        r.setex(
            f"celery-task-name:{task_id}",
            604800,  # 7天过期
            json.dumps({"name": task_name, "task_path": task.name})
        )
    except Exception as e:
        print(f"[Celery] 记录任务名称失败: {e}")

# 定时任务（系统内部调度，非OpenClaw Cron）
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

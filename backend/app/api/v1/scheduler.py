"""
定时任务管理API
从 Celery 配置动态读取任务列表
"""

from fastapi import APIRouter
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import json

from app.tasks.celery_app import celery_app

router = APIRouter(prefix="/scheduler", tags=["定时任务"])


class ScheduledTask(BaseModel):
    """定时任务模型"""
    id: str
    name: str
    description: str
    schedule_type: str  # interval/crontab
    schedule_display: str  # 人类可读的调度描述
    interval_seconds: Optional[int] = None
    crontab: Optional[str] = None
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    status: str  # active/paused/error
    task_module: str
    priority: str  # high/medium/low


class TaskExecution(BaseModel):
    """任务执行记录"""
    task_id: str
    task_name: str
    status: str  # success/failure/running
    started_at: str
    finished_at: Optional[str] = None
    duration: Optional[int] = None  # 秒
    error_message: Optional[str] = None


class SchedulerStatus(BaseModel):
    """调度器状态"""
    is_running: bool
    active_tasks: int
    queued_tasks: int
    last_beat: Optional[str] = None
    uptime: Optional[str] = None


# 任务名称和描述的映射（从 task 模块路径映射到可读信息）
TASK_INFO_MAP = {
    "app.tasks.content_tasks.fetch_analytics": {
        "name": "抓取已发布内容数据",
        "description": "每小时抓取一次已发布内容的点赞、评论、收藏等互动数据，更新内容表现分析",
        "priority": "medium"
    },
    "app.tasks.hotspot_tasks.fetch_hotspots": {
        "name": "热点追踪抓取",
        "description": "每2小时抓取全网热点话题，分析热度趋势，为内容创作提供灵感",
        "priority": "high"
    },
    "app.tasks.hotspot_tasks.send_daily_hotspot_digest": {
        "name": "每日热点精选推送",
        "description": "每晚22:00自动推送当日TOP5热点到飞书，帮助及时了解热门话题",
        "priority": "medium"
    },
    "app.tasks.hotspot_tasks.clean_expired_hotspots": {
        "name": "清理过期热点",
        "description": "每天凌晨3:00清理超过7天的过期热点数据，保持数据库整洁",
        "priority": "low"
    },
    "app.tasks.content_tasks.refresh_xhs_account": {
        "name": "刷新小红书账号数据",
        "description": "每小时从MCP获取最新账号数据（粉丝、笔记、获赞），保持数据实时性",
        "priority": "medium"
    },
    "tasks.fetch_hotspots": {
        "name": "热点追踪抓取",
        "description": "每2小时抓取全网热点话题，分析热度趋势，为内容创作提供灵感",
        "priority": "high"
    },
    "tasks.send_daily_hotspot_digest": {
        "name": "每日热点精选推送",
        "description": "每晚22:00自动推送当日TOP5热点到飞书，帮助及时了解热门话题",
        "priority": "medium"
    },
    "tasks.clean_expired_hotspots": {
        "name": "清理过期热点",
        "description": "每天凌晨3:00清理超过7天的过期热点数据，保持数据库整洁",
        "priority": "low"
    },
    "tasks.refresh_xhs_account": {
        "name": "刷新小红书账号数据",
        "description": "每小时从MCP获取最新账号数据（粉丝、笔记、获赞），保持数据实时性",
        "priority": "medium"
    },
    "app.tasks.content_tasks.generate_content": {
        "name": "生成内容",
        "description": "AI生成小红书内容",
        "priority": "high"
    },
    "app.tasks.content_tasks.publish_content": {
        "name": "发布内容",
        "description": "发布内容到小红书",
        "priority": "high"
    },
    "app.tasks.content_tasks.send_notification": {
        "name": "发送通知",
        "description": "发送系统通知",
        "priority": "low"
    },
}


def parse_schedule(schedule: Any) -> Dict[str, Any]:
    """解析 Celery 的 schedule 配置"""
    result = {
        "schedule_type": "interval",
        "schedule_display": "",
        "interval_seconds": None,
        "crontab": None
    }
    
    if isinstance(schedule, (int, float)):
        # 简单的秒数间隔
        result["interval_seconds"] = int(schedule)
        result["schedule_display"] = format_interval(int(schedule))
    elif isinstance(schedule, str):
        # Crontab 字符串
        result["schedule_type"] = "crontab"
        result["crontab"] = schedule
        result["schedule_display"] = format_crontab(schedule)
    elif hasattr(schedule, 'hour') and hasattr(schedule, 'minute'):
        # Celery crontab 对象
        result["schedule_type"] = "crontab"
        # 处理 hour 可能是 int、list 或 set 的情况
        if isinstance(schedule.hour, int):
            hour = schedule.hour
        elif isinstance(schedule.hour, (list, tuple, set)) and len(schedule.hour) > 0:
            hour = list(schedule.hour)[0]
        else:
            hour = '*'
        # 处理 minute 可能是 int、list 或 set 的情况
        if isinstance(schedule.minute, int):
            minute = schedule.minute
        elif isinstance(schedule.minute, (list, tuple, set)) and len(schedule.minute) > 0:
            minute = list(schedule.minute)[0]
        else:
            minute = '0'
        result["crontab"] = f"{minute} {hour} * * *"
        result["schedule_display"] = f"每天 {hour:02d}:{minute:02d}" if isinstance(hour, int) and isinstance(minute, int) else str(schedule)
    else:
        result["schedule_display"] = str(schedule)
    
    return result


def format_interval(seconds: int) -> str:
    """格式化间隔时间为可读字符串"""
    if seconds == 3600:
        return "每小时"
    elif seconds == 7200:
        return "每2小时"
    elif seconds == 86400:
        return "每天"
    elif seconds == 604800:
        return "每周"
    elif seconds >= 3600:
        return f"每{seconds // 3600}小时"
    elif seconds >= 60:
        return f"每{seconds // 60}分钟"
    else:
        return f"每{seconds}秒"


def format_crontab(crontab_str: str) -> str:
    """格式化 crontab 为可读字符串"""
    if "hour=22" in crontab_str or "22:00" in crontab_str:
        return "每晚 22:00"
    elif "hour=3" in crontab_str or "03:00" in crontab_str:
        return "每天 03:00"
    elif "hour=7" in crontab_str or "07:00" in crontab_str:
        return "每天 07:00"
    else:
        return crontab_str


def calculate_next_run(schedule_info: Dict[str, Any]) -> Optional[datetime]:
    """计算下次执行时间"""
    now = datetime.now()
    
    if schedule_info["schedule_type"] == "interval" and schedule_info["interval_seconds"]:
        interval = schedule_info["interval_seconds"]
        if interval == 3600:  # 每小时
            # 下一个整点
            return now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        elif interval == 7200:  # 每2小时
            # 下一个双数整点
            current_hour = now.hour
            next_hour = ((current_hour // 2) + 1) * 2
            if next_hour >= 24:
                next_hour = 0
                tomorrow = now + timedelta(days=1)
                return tomorrow.replace(hour=next_hour, minute=0, second=0, microsecond=0)
            else:
                return now.replace(hour=next_hour, minute=0, second=0, microsecond=0)
        else:
            # 其他间隔
            return now + timedelta(seconds=interval - (now.timestamp() % interval))
    
    elif schedule_info["schedule_type"] == "crontab":
        crontab = schedule_info.get("crontab", "")
        if "22" in crontab:
            next_run = now.replace(hour=22, minute=0, second=0, microsecond=0)
            if next_run < now:
                next_run = next_run + timedelta(days=1)
            return next_run
        elif "3" in crontab:
            next_run = now.replace(hour=3, minute=0, second=0, microsecond=0)
            if next_run < now:
                next_run = next_run + timedelta(days=1)
            return next_run
    
    return None


@router.get("/tasks", response_model=dict)
async def get_scheduled_tasks():
    """
    从 Celery 配置动态获取所有定时任务列表
    """
    # 从 Celery app 读取 beat_schedule 配置
    beat_schedule = celery_app.conf.get("beat_schedule", {})
    
    tasks = []
    for task_id, config in beat_schedule.items():
        task_path = config.get("task", "")
        schedule = config.get("schedule")
        
        # 获取任务信息
        task_info = TASK_INFO_MAP.get(task_path, {
            "name": task_id.replace("-", " ").title(),
            "description": f"定时执行: {task_path}",
            "priority": "medium"
        })
        
        # 解析调度规则
        schedule_info = parse_schedule(schedule)
        
        # 计算下次执行时间
        next_run = calculate_next_run(schedule_info)
        
        tasks.append({
            "id": task_id,
            "name": task_info["name"],
            "description": task_info["description"],
            "schedule_type": schedule_info["schedule_type"],
            "schedule_display": schedule_info["schedule_display"],
            "interval_seconds": schedule_info["interval_seconds"],
            "crontab": schedule_info["crontab"],
            "status": "active",
            "task_module": task_path,
            "priority": task_info["priority"],
            "last_run": None,
            "next_run": next_run.isoformat() if next_run else None
        })
    
    return {
        "code": 200,
        "data": {
            "tasks": tasks,
            "total": len(tasks)
        },
        "message": "success"
    }


@router.get("/status", response_model=dict)
async def get_scheduler_status():
    """
    获取调度器状态
    """
    # 尝试从 Celery 获取活跃任务数
    try:
        import redis
        r = redis.from_url(celery_app.conf.result_backend)
        active_tasks = len([k for k in r.scan_iter(match="celery-task-meta-*")])
    except:
        active_tasks = 0
    
    return {
        "code": 200,
        "data": {
            "is_running": True,
            "active_tasks": active_tasks,
            "queued_tasks": 0,
            "last_beat": datetime.now().isoformat(),
            "uptime": "运行中"
        },
        "message": "success"
    }


@router.get("/executions", response_model=dict)
async def get_task_executions(limit: int = 20):
    """
    获取任务执行历史（从 Redis 读取真实的 Celery 任务结果）
    """
    executions = []
    
    try:
        import redis
        r = redis.from_url(celery_app.conf.result_backend)
        
        # 获取最近的任务结果
        task_keys = list(r.scan_iter(match="celery-task-meta-*", count=limit * 2))
        
        for key in task_keys[:limit]:
            try:
                task_data = r.get(key)
                if task_data:
                    task_info = json.loads(task_data)
                    task_id = key.decode().replace("celery-task-meta-", "")
                    
                    # 获取任务名称 - 优先从任务名称映射中读取
                    task_name = "未知任务"
                    
                    # 1. 首先尝试从 Redis 读取任务名称映射（由 task_prerun 信号记录）
                    try:
                        name_data = r.get(f"celery-task-name:{task_id}")
                        if name_data:
                            name_info = json.loads(name_data)
                            task_name = name_info.get("name", "未知任务")
                    except Exception as e:
                        print(f"[Scheduler] 读取任务名称映射失败: {e}")
                    
                    # 2. 如果没有映射，尝试从任务结果推断
                    if task_name == "未知任务":
                        task_path = task_info.get("task", "")
                        if task_path and task_path in TASK_INFO_MAP:
                            task_name = TASK_INFO_MAP[task_path]["name"]
                        else:
                            # 通过结果内容推断任务类型
                            result = task_info.get("result", {})
                            if isinstance(result, dict):
                                # 如果有 nickname/followers，说明是账号刷新任务
                                if "nickname" in result or "followers" in result:
                                    task_name = "刷新小红书账号数据"
                                # 如果有热点相关字段，说明是热点任务
                                elif "hotspots" in result or "count" in result and isinstance(result.get("count"), int):
                                    task_name = "热点追踪抓取"
                                # 默认显示为定时任务
                                else:
                                    task_name = "定时任务执行"
                            elif task_info.get("traceback"):
                                task_name = "定时任务执行"
                    
                    # Celery 返回的 date_done 是 UTC 时间，需要转换为北京时间
                    from datetime import timezone
                    date_done_utc = task_info.get("date_done")
                    if date_done_utc:
                        # 解析 UTC 时间并转换为北京时间 (+8)
                        dt = datetime.fromisoformat(date_done_utc.replace('Z', '+00:00'))
                        dt_beijing = dt.astimezone(timezone(timedelta(hours=8)))
                        started_at = dt_beijing.strftime("%Y-%m-%dT%H:%M:%S")
                    else:
                        started_at = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                    
                    executions.append({
                        "task_id": task_id,
                        "task_name": task_name,
                        "status": "success" if task_info.get("status") == "SUCCESS" else "failure",
                        "started_at": started_at,
                        "finished_at": started_at,
                        "duration": task_info.get("result", {}).get("duration") if isinstance(task_info.get("result"), dict) else None,
                        "error_message": task_info.get("traceback") if task_info.get("status") == "FAILURE" else None
                    })
            except Exception as e:
                print(f"[Scheduler] 解析任务结果失败: {e}")
                continue
        
        # 按时间倒序
        executions.sort(key=lambda x: x["started_at"], reverse=True)
        
    except Exception as e:
        print(f"[Scheduler] 读取任务历史失败: {e}")
    
    return {
        "code": 200,
        "data": {
            "executions": executions,
            "total": len(executions)
        },
        "message": "success"
    }


@router.post("/tasks/{task_id}/run", response_model=dict)
async def run_task_now(task_id: str):
    """
    立即执行指定任务（手动触发）
    """
    # 从 Celery 配置中查找任务
    beat_schedule = celery_app.conf.get("beat_schedule", {})
    
    if task_id not in beat_schedule:
        return {
            "code": 404,
            "data": None,
            "message": "任务不存在"
        }
    
    task_config = beat_schedule[task_id]
    task_path = task_config.get("task")
    
    try:
        # 发送任务到队列
        result = celery_app.send_task(task_path)
        return {
            "code": 200,
            "data": {
                "task_id": task_id,
                "celery_task_id": result.id,
                "status": "queued"
            },
            "message": "任务已加入队列"
        }
    except Exception as e:
        return {
            "code": 500,
            "data": None,
            "message": f"启动任务失败: {str(e)}"
        }

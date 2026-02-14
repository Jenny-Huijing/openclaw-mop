"""
统计API路由
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import Task, Content, HotTopic as Hotspot
from app.schemas import StatsOverview, ApiResponse

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/overview", response_model=ApiResponse)
async def get_overview(
    db: AsyncSession = Depends(get_db)
):
    """数据概览"""
    # 任务统计
    tasks_result = await db.execute(select(Task))
    all_tasks = tasks_result.scalars().all()
    
    total_tasks = len(all_tasks)
    pending_tasks = sum(1 for t in all_tasks if t.status == "pending")
    doing_tasks = sum(1 for t in all_tasks if t.status == "doing")
    review_tasks = sum(1 for t in all_tasks if t.status == "review")
    ready_tasks = sum(1 for t in all_tasks if t.status == "ready")
    
    # 今日发布
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_published = sum(
        1 for t in all_tasks 
        if t.status == "published" and t.completed_at and t.completed_at >= today
    )
    
    # 内容统计
    contents_result = await db.execute(select(Content))
    total_contents = len(contents_result.scalars().all())
    
    # 热点统计
    hotspots_result = await db.execute(select(Hotspot))
    total_hotspots = len(hotspots_result.scalars().all())
    
    return ApiResponse(
        data={
            "tasks": {
                "total": total_tasks,
                "pending": pending_tasks,
                "doing": doing_tasks,
                "review": review_tasks,
                "ready": ready_tasks,
                "today_published": today_published
            },
            "contents": {
                "total": total_contents
            },
            "hotspots": {
                "total": total_hotspots
            }
        }
    )


@router.get("/tasks", response_model=ApiResponse)
async def get_task_stats(
    days: int = 7,
    db: AsyncSession = Depends(get_db)
):
    """任务统计"""
    # 最近N天的任务趋势
    start_date = datetime.now() - timedelta(days=days)
    
    # 按天统计
    result = await db.execute(
        select(
            func.date(Task.created_at).label("date"),
            func.count(Task.id).label("count"),
            func.sum(func.case((Task.status == "published", 1), else_=0)).label("published")
        )
        .where(Task.created_at >= start_date)
        .group_by(func.date(Task.created_at))
        .order_by("date")
    )
    
    daily_stats = result.all()
    
    return ApiResponse(
        data={
            "days": days,
            "daily": [
                {
                    "date": str(row.date),
                    "created": row.count,
                    "published": row.published or 0
                }
                for row in daily_stats
            ]
        }
    )


@router.get("/contents", response_model=ApiResponse)
async def get_content_stats(
    db: AsyncSession = Depends(get_db)
):
    """内容统计"""
    # 按状态统计
    result = await db.execute(
        select(Content.status, func.count(Content.id))
        .group_by(Content.status)
    )
    status_counts = {row[0]: row[1] for row in result.all()}
    
    # 平台统计
    platform_result = await db.execute(
        select(Content.platform, func.count(Content.id))
        .group_by(Content.platform)
    )
    platform_counts = {row[0]: row[1] for row in platform_result.all()}
    
    return ApiResponse(
        data={
            "by_status": status_counts,
            "by_platform": platform_counts
        }
    )

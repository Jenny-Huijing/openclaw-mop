"""
任务API路由
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import Task, Content
from app.schemas import TaskCreate, TaskUpdate, TaskResponse, ApiResponse

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=ApiResponse)
async def list_tasks(
    status: Optional[str] = Query(None, description="任务状态过滤"),
    priority: Optional[str] = Query(None, description="优先级过滤"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """获取任务列表"""
    query = select(Task).order_by(desc(Task.created_at))
    
    if status:
        query = query.where(Task.status == status)
    if priority:
        query = query.where(Task.priority == priority)
    
    # 计数
    count_query = select(Task)
    if status:
        count_query = count_query.where(Task.status == status)
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())
    
    # 分页
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    return ApiResponse(
        data={
            "items": [task.to_dict() for task in tasks],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    )


@router.post("", response_model=ApiResponse)
async def create_task(
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建任务"""
    task = Task(
        title=task_data.title,
        topic=task_data.topic,
        type=task_data.type,
        priority=task_data.priority,
        scheduled_at=task_data.scheduled_at,
        source=task_data.source,
        payload=task_data.payload,
        status="pending"
    )
    
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    return ApiResponse(
        message="任务创建成功",
        data=task.to_dict()
    )


@router.get("/{task_id}", response_model=ApiResponse)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取任务详情"""
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return ApiResponse(data=task.to_dict())


@router.put("/{task_id}", response_model=ApiResponse)
async def update_task(
    task_id: str,
    task_data: TaskUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新任务"""
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 更新字段
    if task_data.status:
        task.status = task_data.status
    if task_data.priority:
        task.priority = task_data.priority
    if task_data.scheduled_at is not None:
        task.scheduled_at = task_data.scheduled_at
    if task_data.result:
        task.result = task_data.result
    
    await db.commit()
    await db.refresh(task)
    
    return ApiResponse(
        message="任务更新成功",
        data=task.to_dict()
    )


@router.delete("/{task_id}", response_model=ApiResponse)
async def delete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除任务"""
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    await db.delete(task)
    await db.commit()
    
    return ApiResponse(message="任务删除成功")

"""
Pydantic模型 - 任务相关
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ========== 基础 ==========
class BaseSchema(BaseModel):
    """基础模型"""
    class Config:
        from_attributes = True


# ========== 任务 ==========
class TaskBase(BaseSchema):
    """任务基础"""
    title: str = Field(..., min_length=1, max_length=200)
    topic: Optional[str] = Field(None, max_length=50)
    priority: str = Field(default="medium", pattern="^(low|medium|high|urgent)$")
    scheduled_at: Optional[datetime] = None


class TaskCreate(TaskBase):
    """创建任务"""
    type: str = Field(..., pattern="^(hotspot_analysis|content_creation|publish)$")
    source: Optional[str] = "manual"
    payload: dict = Field(default_factory=dict)


class TaskUpdate(BaseSchema):
    """更新任务"""
    status: Optional[str] = Field(None, pattern="^(pending|doing|review|ready|published|failed|cancelled)$")
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|urgent)$")
    scheduled_at: Optional[datetime] = None
    result: Optional[dict] = None


class TaskResponse(TaskBase):
    """任务响应"""
    id: str
    type: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    source: Optional[str]
    retry_count: int
    created_at: datetime
    updated_at: datetime


class TaskListResponse(BaseSchema):
    """任务列表响应"""
    items: List[TaskResponse]
    total: int


# ========== 内容 ==========
class ContentBase(BaseSchema):
    """内容基础"""
    title: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1)
    tags: Optional[List[str]] = Field(default_factory=list)


class ContentCreate(ContentBase):
    """创建内容"""
    task_id: Optional[str] = None
    word_count: Optional[int] = None


class ContentUpdate(BaseSchema):
    """更新内容"""
    title: Optional[str] = Field(None, max_length=200)
    body: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = Field(None, pattern="^(draft|review|ready|published|rejected)$")


class ContentResponse(ContentBase):
    """内容响应"""
    id: str
    task_id: Optional[str]
    status: str
    platform: str
    platform_content_id: Optional[str]
    published_at: Optional[datetime]
    analytics: dict
    word_count: Optional[int]
    created_at: datetime
    updated_at: datetime


# ========== 热点 ==========
class HotspotBase(BaseSchema):
    """热点基础"""
    title: str = Field(..., min_length=1, max_length=200)
    category: Optional[str] = Field(None, max_length=50)


class HotspotCreate(HotspotBase):
    """创建热点"""
    heat_score: Optional[int] = Field(None, ge=0, le=100)
    match_score: Optional[int] = Field(None, ge=0, le=100)
    source: Optional[str] = None
    source_urls: Optional[List[str]] = Field(default_factory=list)
    angle: Optional[str] = None


class HotspotResponse(HotspotBase):
    """热点响应"""
    id: str
    heat_score: Optional[int]
    match_score: Optional[int]
    source: Optional[str]
    source_urls: Optional[List[str]]
    angle: Optional[str]
    analyzed_at: Optional[datetime]
    created_task_id: Optional[str]
    created_at: datetime


# ========== 统计 ==========
class StatsOverview(BaseSchema):
    """数据概览"""
    total_tasks: int
    pending_tasks: int
    review_tasks: int
    published_today: int
    total_contents: int
    total_hotspots: int


# ========== 通用响应 ==========
class ApiResponse(BaseSchema):
    """API通用响应"""
    code: int = 200
    message: str = "success"
    data: Optional[dict] = None

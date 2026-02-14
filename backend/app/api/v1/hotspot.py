"""
热点API路由
"""
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas import ApiResponse
from app.services.hotspot_service import hotspot_service

router = APIRouter(prefix="/hotspots", tags=["热点"])


@router.get("", response_model=ApiResponse)
async def list_hotspots(
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """获取热点列表"""
    hotspots = await hotspot_service.get_hotspots(limit=limit, category=category)
    return ApiResponse(
        data={
            "items": hotspots,
            "total": len(hotspots)
        }
    )


@router.get("/{topic_id}/trend", response_model=ApiResponse)
async def get_hotspot_trend(
    topic_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取热点趋势"""
    trends = await hotspot_service.get_trend(topic_id)
    return ApiResponse(data=trends)


@router.post("/{topic_id}/adopt", response_model=ApiResponse)
async def adopt_hotspot(
    topic_id: str,
    db: AsyncSession = Depends(get_db)
):
    """采纳热点，创建创作任务"""
    from app.agents.orchestrator import orchestrator
    from app.models import Content
    import asyncio
    
    try:
        # 先创建内容记录（标记为创作中）
        workflow_id = f"wf_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        content = Content(
            id=str(uuid.uuid4()),
            title="创作中...",
            titles=["创作中..."],
            body="AI正在为您生成内容，请稍候...",
            status="CREATING",
            workflow_id=workflow_id,
            source_type="hotspot",
            source_id=topic_id,
            created_at=datetime.now()
        )
        db.add(content)
        await db.commit()
        await db.refresh(content)
        
        # 异步执行 workflow
        async def run_workflow():
            try:
                result = await orchestrator.run(user_id="default")
                content_data = result.get("content", {})
                
                # 使用新的数据库会话更新内容
                from app.core.database import async_session_maker
                async with async_session_maker() as session:
                    from sqlalchemy import select
                    result = await session.execute(
                        select(Content).where(Content.id == content.id)
                    )
                    content_record = result.scalar_one_or_none()
                    
                    if content_record:
                        content_record.titles = content_data.get("titles", [])
                        content_record.title = content_data.get("titles", [""])[0] if content_data.get("titles") else "无标题"
                        content_record.body = content_data.get("body", "")
                        content_record.tags = content_data.get("tags", [])
                        content_record.image_prompts = content_data.get("image_prompts", [])
                        content_record.images = content_data.get("images", [])
                        content_record.status = "reviewing"
                        await session.commit()
                        print(f"[Adopt] 内容 {content.id} 创作完成")
            except Exception as e:
                print(f"[Adopt] Workflow 执行失败: {e}")
                import traceback
                traceback.print_exc()
                # 标记为失败
                try:
                    from app.core.database import async_session_maker
                    async with async_session_maker() as session:
                        from sqlalchemy import select
                        result = await session.execute(
                            select(Content).where(Content.id == content.id)
                        )
                        content_record = result.scalar_one_or_none()
                        if content_record:
                            content_record.status = "failed"
                            content_record.body = f"生成失败: {str(e)}"
                            await session.commit()
                except Exception as inner_e:
                    print(f"[Adopt] 标记失败状态也失败了: {inner_e}")
        
        # 启动异步任务
        asyncio.create_task(run_workflow())
        
        return ApiResponse(
            message="创作任务已启动",
            data={
                "content_id": content.id,
                "workflow_id": workflow_id,
                "status": "CREATING"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fetch", response_model=ApiResponse)
async def manual_fetch_hotspots(
    db: AsyncSession = Depends(get_db)
):
    """手动触发热点抓取（调试用）"""
    await hotspot_service.fetch_and_update_hotspots()
    return ApiResponse(message="热点抓取已触发")


@router.get("/stats/overview", response_model=ApiResponse)
async def get_hotspot_stats(
    db: AsyncSession = Depends(get_db)
):
    """获取热点统计"""
    from sqlalchemy import select, func
    from app.models.hotspot import HotTopic
    
    # 统计各分类数量
    result = await db.execute(
        select(HotTopic.category, func.count(HotTopic.id))
        .where(HotTopic.status == "active")
        .group_by(HotTopic.category)
    )
    
    stats = {category: count for category, count in result.all()}
    
    # 今日新增
    from datetime import datetime, timedelta
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_result = await db.execute(
        select(func.count(HotTopic.id))
        .where(HotTopic.discovered_at >= today)
    )
    today_count = today_result.scalar()
    
    return ApiResponse(
        data={
            "categories": stats,
            "today_new": today_count,
            "total_active": sum(stats.values())
        }
    )

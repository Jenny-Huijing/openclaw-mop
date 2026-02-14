"""
小红书自动发布 API
真正调用 MCP 发布内容，并同步更新平台记录
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

from app.core.database import get_db
from app.models import Content
from app.schemas import ApiResponse
from app.services.xhs_publisher import get_publisher
from app.services.xhs_crawler import fetch_account_stats

router = APIRouter(prefix="/contents", tags=["contents"])


@router.post("/{content_id}/auto-publish", response_model=ApiResponse)
async def auto_publish_content(
    content_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    自动发布内容到小红书
    
    流程：
    1. 调用 MCP publish_content 工具发布
    2. 发布成功后更新数据库状态为 published
    3. 异步刷新小红书账号数据
    
    **注意**: 此操作会实际发布内容到小红书账号！
    """
    # 获取内容
    result = await db.execute(
        select(Content).where(Content.id == content_id)
    )
    content = result.scalar_one_or_none()
    
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")
    
    if content.status == "published":
        raise HTTPException(status_code=400, detail="内容已发布，请勿重复发布")
    
    if content.status not in ["approved", "reviewing"]:
        raise HTTPException(status_code=400, detail="内容状态不正确，请先审核通过")
    
    # 准备发布数据
    title = content.titles[0] if content.titles else "无标题"
    body = content.body or ""
    tags = content.tags or []
    
    # 处理配图
    images = []
    if content.images:
        for img in content.images:
            if isinstance(img, dict):
                # 优先使用本地路径
                if img.get("local_path"):
                    images.append(img["local_path"])
                elif img.get("url"):
                    images.append(img["url"])
    
    if not images:
        raise HTTPException(status_code=400, detail="内容没有配图，无法发布")
    
    # 调用 MCP 发布
    publisher = get_publisher()
    publish_result = await publisher.publish_note(
        title=title,
        content=body,
        images=images,
        tags=tags
    )
    
    if not publish_result.get("success"):
        error_msg = publish_result.get("error", "未知错误")
        raise HTTPException(status_code=500, detail=f"发布失败: {error_msg}")
    
    # 发布成功，更新数据库状态
    content.status = "published"
    content.published_at = datetime.now()
    await db.commit()
    await db.refresh(content)
    
    # 异步刷新小红书账号数据
    background_tasks.add_task(refresh_account_stats_async)
    
    return ApiResponse(
        message="内容已成功发布到小红书",
        data={
            "content": content.to_dict(),
            "publish_result": publish_result
        }
    )


async def refresh_account_stats_async():
    """异步刷新小红书账号数据"""
    try:
        # 等待几秒让小红书数据更新
        await asyncio.sleep(5)
        
        # 清除缓存
        from app.api.v1 import xhs as xhs_module
        xhs_module._cached_stats = None
        xhs_module._cache_time = 0
        
        # 重新获取数据
        await fetch_account_stats()
        print(f"[XHS] 发布内容后自动刷新账号数据成功")
    except Exception as e:
        print(f"[XHS] 发布内容后刷新账号数据失败: {e}")

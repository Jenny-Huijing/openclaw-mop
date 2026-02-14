"""
内容API路由 - 适配新版 Content 模型
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, async_session_maker
from app.models import Content
from app.schemas import ApiResponse

router = APIRouter(prefix="/contents", tags=["contents"])


@router.get("", response_model=ApiResponse)
async def list_contents(
    status: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """获取内容列表"""
    query = select(Content).order_by(desc(Content.created_at))
    
    if status:
        query = query.where(Content.status == status)
    
    # 计数
    count_query = select(Content)
    if status:
        count_query = count_query.where(Content.status == status)
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())
    
    # 分页
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    contents = result.scalars().all()
    
    return ApiResponse(
        data={
            "items": [content.to_dict() for content in contents],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    )


@router.get("/{content_id}", response_model=ApiResponse)
async def get_content(
    content_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取内容详情"""
    result = await db.execute(
        select(Content).where(Content.id == content_id)
    )
    content = result.scalar_one_or_none()
    
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")
    
    return ApiResponse(data=content.to_dict())


@router.post("/{content_id}/approve", response_model=ApiResponse)
async def approve_content(
    content_id: str,
    db: AsyncSession = Depends(get_db)
):
    """审核通过内容并自动发布"""
    result = await db.execute(
        select(Content).where(Content.id == content_id)
    )
    content = result.scalar_one_or_none()
    
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")
    
    # 标记为 approved
    content.status = "approved"
    content.approved_at = datetime.now()
    await db.commit()
    await db.refresh(content)
    
    # 自动发布到小红书
    try:
        from app.services.xhs_mcp import mcp_service
        
        publish_result = await mcp_service.publish_note(
            title=content.titles[0] if content.titles else "",
            content=content.body or "",
            images=[img.get("url", img) if isinstance(img, dict) else img for img in (content.images or [])]
        )
        
        if publish_result.get("success"):
            content.status = "published"
            content.published_at = datetime.now()
            content.error_message = None
            await db.commit()
            await db.refresh(content)
            
            return ApiResponse(
                message="✅ 审核通过并自动发布成功！",
                data=content.to_dict()
            )
        else:
            # 发布失败，但审核已通过
            error_msg = publish_result.get("error", "发布失败")
            content.status = "PUBLISH_FAILED"
            content.error_message = error_msg[:500]
            await db.commit()
            await db.refresh(content)
            
            return ApiResponse(
                message=f"⚠️ 审核通过，但自动发布失败: {error_msg}",
                data=content.to_dict()
            )
            
    except Exception as e:
        # 发布异常，但审核已通过
        content.status = "PUBLISH_FAILED"
        content.error_message = str(e)[:500]
        await db.commit()
        await db.refresh(content)
        
        return ApiResponse(
            message=f"⚠️ 审核通过，但自动发布失败: {str(e)}",
            data=content.to_dict()
        )


@router.post("/{content_id}/reject", response_model=ApiResponse)
async def reject_content(
    content_id: str,
    db: AsyncSession = Depends(get_db)
):
    """拒绝内容"""
    result = await db.execute(
        select(Content).where(Content.id == content_id)
    )
    content = result.scalar_one_or_none()
    
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")
    
    content.status = "rejected"
    await db.commit()
    await db.refresh(content)
    
    return ApiResponse(
        message="已拒绝",
        data=content.to_dict()
    )


@router.post("/{content_id}/publish", response_model=ApiResponse)
async def publish_content(
    content_id: str,
    db: AsyncSession = Depends(get_db)
):
    """发布内容（标记为已发布）"""
    result = await db.execute(
        select(Content).where(Content.id == content_id)
    )
    content = result.scalar_one_or_none()
    
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")
    
    if content.status != "approved":
        raise HTTPException(status_code=400, detail="内容未审核通过")
    
    content.status = "published"
    content.published_at = datetime.now()
    await db.commit()
    await db.refresh(content)
    
    return ApiResponse(
        message="发布成功",
        data=content.to_dict()
    )


@router.post("/{content_id}/auto-publish", response_model=ApiResponse)
async def auto_publish_content(
    content_id: str,
    db: AsyncSession = Depends(get_db)
):
    """自动发布内容（通过 MCP 发布到小红书）"""
    result = await db.execute(
        select(Content).where(Content.id == content_id)
    )
    content = result.scalar_one_or_none()
    
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")
    
    if content.status != "approved":
        raise HTTPException(status_code=400, detail="内容未审核通过")
    
    # 尝试通过 MCP 发布
    try:
        from app.services.xhs_mcp import mcp_service
        
        publish_result = await mcp_service.publish_note(
            title=content.titles[0] if content.titles else "",
            content=content.body or "",
            images=[img.get("url", img) if isinstance(img, dict) else img for img in (content.images or [])]
        )
        
        if publish_result.get("success"):
            content.status = "published"
            content.published_at = datetime.now()
            content.error_message = None  # 清除之前的错误
            await db.commit()
            await db.refresh(content)
            
            return ApiResponse(
                message="发布成功",
                data=content.to_dict()
            )
        else:
            # MCP 返回失败，记录失败状态和原因
            error_msg = publish_result.get("error", "发布失败")
            content.status = "PUBLISH_FAILED"
            content.error_message = error_msg[:500]
            await db.commit()
            await db.refresh(content)
            
            raise HTTPException(status_code=500, detail=f"发布失败: {error_msg}")
            
    except Exception as e:
        # MCP 发布失败，标记为发布失败状态并记录原因
        content.status = "PUBLISH_FAILED"
        content.error_message = str(e)[:500]  # 限制长度
        await db.commit()
        await db.refresh(content)
        
        raise HTTPException(
            status_code=500, 
            detail=f"自动发布失败: {str(e)}，已标记为发布失败，可查看错误原因后重试或手动发布"
        )


@router.post("/{content_id}/regenerate", response_model=ApiResponse)
async def regenerate_content(
    content_id: str,
    db: AsyncSession = Depends(get_db)
):
    """重新创作内容 - 触发新的 workflow 生成新内容"""
    result = await db.execute(
        select(Content).where(Content.id == content_id)
    )
    content = result.scalar_one_or_none()
    
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")
    
    # 将内容状态改为创作中，触发重新创作
    content.status = "CREATING"
    content.body = "AI正在重新创作内容，请稍候..."
    content.titles = ["重新创作中..."]
    await db.commit()
    await db.refresh(content)
    
    # 异步触发新的 workflow（使用新的数据库会话）
    import asyncio
    from app.agents.orchestrator import orchestrator
    from app.core.database import async_session_maker
    
    async def run_regenerate():
        """在后台执行重新创作，使用独立的数据库会话"""
        try:
            print(f"[Regenerate] 开始重新创作内容 {content_id}")
            # 使用原内容的 workflow_id，确保 publish_node 能找到对应记录
            workflow_result = await orchestrator.run(user_id="default", workflow_id=content.workflow_id)
            
            content_data = workflow_result.get("content", {})
            workflow_id = workflow_result.get("workflow_id", "")
            
            # 使用新的数据库会话更新内容
            async with async_session_maker() as session:
                # 重新查询内容（避免会话问题）
                from sqlalchemy import select
                db_result = await session.execute(
                    select(Content).where(Content.id == content_id)
                )
                content = db_result.scalar_one_or_none()
                
                if content:
                    # 验证内容有效性
                    titles = content_data.get("titles", [])
                    body = content_data.get("body", "")
                    if not titles or not body or len(body) < 10:
                        raise Exception(f"重新创作失败: 内容不完整 (titles={len(titles)}, body={len(body)} 字符)")
                    
                    # 更新内容
                    content.titles = titles
                    content.body = body
                    content.tags = content_data.get("tags", [])
                    content.image_prompts = content_data.get("image_prompts", [])
                    content.images = content_data.get("images", [])
                    content.status = "reviewing"
                    await session.commit()
                    print(f"[Regenerate] 内容 {content_id} 重新创作完成")
                else:
                    print(f"[Regenerate] 内容 {content_id} 未找到")
                    
        except Exception as e:
            print(f"[Regenerate] 内容 {content_id} 重新创作失败: {e}")
            import traceback
            traceback.print_exc()
            # 使用新的数据库会话标记为失败
            try:
                async with async_session_maker() as session:
                    from sqlalchemy import select
                    db_result = await session.execute(
                        select(Content).where(Content.id == content_id)
                    )
                    content = db_result.scalar_one_or_none()
                    if content:
                        content.status = "failed"
                        content.body = f"重新创作失败: {str(e)}"
                        await session.commit()
            except Exception as inner_e:
                print(f"[Regenerate] 标记失败状态也失败了: {inner_e}")
    
    # 异步执行
    asyncio.create_task(run_regenerate())
    
    return ApiResponse(
        message="重新创作任务已启动",
        data=content.to_dict()
    )


@router.post("/{content_id}/publish-to-xhs", response_model=ApiResponse)
async def publish_content_to_xhs(
    content_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    标记内容为已发布到小红书
    
    **注意**: 此接口仅标记状态，实际发布需要手动操作或使用其他工具
    
    建议发布流程：
    1. 在本平台生成内容并审核通过
    2. 复制内容到小红书创作平台手动发布
    3. 调用此接口标记为已发布
    
    **自动触发**: 发布后会自动刷新小红书账号数据
    """
    # 获取内容
    result = await db.execute(
        select(Content).where(Content.id == content_id)
    )
    content = result.scalar_one_or_none()
    
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")
    
    if content.status != "approved":
        raise HTTPException(status_code=400, detail="内容未审核通过，请先审核")
    
    # 更新为已发布状态
    content.status = "published"
    content.published_at = datetime.now()
    await db.commit()
    await db.refresh(content)
    
    # 准备发布信息
    import re
    topics = re.findall(r'#([^#\s]+)#', content.body or "")
    
    # 发布成功后，异步刷新小红书账号数据
    import asyncio
    from app.services.xhs_crawler import fetch_account_stats
    
    async def refresh_stats_async():
        """异步刷新账号数据"""
        try:
            # 清除 xhs.py 中的缓存
            from app.api.v1 import xhs as xhs_module
            xhs_module._cached_stats = None
            xhs_module._cache_time = 0
            
            # 重新获取数据
            await fetch_account_stats()
            print(f"[XHS] 发布内容后自动刷新账号数据成功")
        except Exception as e:
            print(f"[XHS] 发布内容后刷新账号数据失败: {e}")
    
    # 异步执行刷新（不阻塞响应）
    asyncio.create_task(refresh_stats_async())
    
    return ApiResponse(
        message="内容已标记为已发布到小红书，账号数据正在刷新",
        data={
            "content": content.to_dict(),
            "publish_info": {
                "title": content.title,
                "content": content.body,
                "topics": topics,
                "cover_image": content.cover_image
            }
        }
    )


@router.delete("/{content_id}", response_model=ApiResponse)
async def delete_content(
    content_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除内容（仅允许删除失败或创建中的内容）"""
    result = await db.execute(
        select(Content).where(Content.id == content_id)
    )
    content = result.scalar_one_or_none()
    
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")
    
    # 只允许删除失败或创建中的内容
    if content.status not in ["failed", "CREATING", "creating"]:
        raise HTTPException(status_code=400, detail="只能删除失败或创作中的内容")
    
    await db.delete(content)
    await db.commit()
    
    return ApiResponse(message="内容已删除")

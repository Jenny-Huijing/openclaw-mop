"""
Publisher Agent - 自动发布到小红书
基于 LangGraph 的发布节点
"""

import asyncio
from typing import TypedDict, Optional, Dict
from datetime import datetime

from app.services.xhs_mcp import mcp_service
from app.core.database import async_session_maker
from app.models import Content


class PublishState(TypedDict):
    """发布状态"""
    content_id: str
    title: str
    body: str
    images: list
    tags: list
    publish_result: Optional[Dict]
    error: Optional[str]
    retry_count: int


class PublisherAgent:
    """
    自动发布 Agent
    负责将内容发布到小红书平台
    """
    
    MAX_RETRIES = 3
    
    async def publish(self, content_id: str) -> Dict:
        """
        执行发布流程
        
        Args:
            content_id: 内容ID
            
        Returns:
            发布结果
        """
        print(f"[PublisherAgent] 开始发布内容 {content_id}")
        
        # 获取内容详情
        async with async_session_maker() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Content).where(Content.id == content_id)
            )
            content = result.scalar_one_or_none()
            
            if not content:
                return {"success": False, "error": "内容不存在"}
            
            if content.status != "approved":
                return {"success": False, "error": f"内容状态不正确: {content.status}"}
            
            # 准备发布数据
            title = content.titles[0] if content.titles else ""
            body = content.body or ""
            images = content.images or []
            tags = content.tags or []
            
            print(f"[PublisherAgent] 标题: {title[:30]}...")
            print(f"[PublisherAgent] 图片数量: {len(images)}")
            print(f"[PublisherAgent] 标签: {tags}")
        
        # 执行发布（带重试）
        for attempt in range(self.MAX_RETRIES):
            try:
                print(f"[PublisherAgent] 第 {attempt + 1} 次尝试发布...")
                
                # 调用 MCP 发布
                result = await mcp_service.publish_note(
                    title=title,
                    content=body,
                    images=[img.get("url", img) if isinstance(img, dict) else img for img in images],
                    tags=tags
                )
                
                if result.get("success"):
                    print(f"[PublisherAgent] 发布成功!")
                    
                    # 更新数据库状态
                    async with async_session_maker() as session:
                        from sqlalchemy import select
                        result = await session.execute(
                            select(Content).where(Content.id == content_id)
                        )
                        content = result.scalar_one_or_none()
                        
                        if content:
                            content.status = "published"
                            content.published_at = datetime.now()
                            await session.commit()
                    
                    return {
                        "success": True,
                        "content_id": content_id,
                        "published_at": datetime.now().isoformat()
                    }
                else:
                    error = result.get("error", "未知错误")
                    print(f"[PublisherAgent] 发布失败: {error}")
                    
                    if attempt < self.MAX_RETRIES - 1:
                        wait_time = 2 ** attempt  # 指数退避
                        print(f"[PublisherAgent] {wait_time}秒后重试...")
                        await asyncio.sleep(wait_time)
                    else:
                        # 最后一次失败，标记为发布失败
                        async with async_session_maker() as session:
                            from sqlalchemy import select
                            result = await session.execute(
                                select(Content).where(Content.id == content_id)
                            )
                            content = result.scalar_one_or_none()
                            
                            if content:
                                content.status = "publish_failed"
                                await session.commit()
                        
                        return {
                            "success": False,
                            "error": error,
                            "content_id": content_id
                        }
                        
            except Exception as e:
                print(f"[PublisherAgent] 发布异常: {e}")
                import traceback
                traceback.print_exc()
                
                if attempt < self.MAX_RETRIES - 1:
                    wait_time = 2 ** attempt
                    print(f"[PublisherAgent] {wait_time}秒后重试...")
                    await asyncio.sleep(wait_time)
                else:
                    # 最后一次失败
                    async with async_session_maker() as session:
                        from sqlalchemy import select
                        result = await session.execute(
                            select(Content).where(Content.id == content_id)
                        )
                        content = result.scalar_one_or_none()
                        
                        if content:
                            content.status = "publish_failed"
                            await session.commit()
                    
                    return {
                        "success": False,
                        "error": str(e),
                        "content_id": content_id
                    }
        
        return {"success": False, "error": "重试次数已用完"}


# 单例
publisher_agent = PublisherAgent()

"""
热点追踪定时任务
"""
from celery import shared_task
from datetime import datetime
import asyncio


@shared_task(name="tasks.fetch_hotspots")
def fetch_hotspots():
    """
    抓取热点任务
    每2小时执行一次（7:00-23:00）
    """
    print(f"[Celery] 执行热点抓取任务: {datetime.now()}")
    
    from app.services.hotspot_service import hotspot_service
    
    # 创建新的事件循环避免冲突
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(hotspot_service.fetch_and_update_hotspots())
        return {"status": "success", "time": datetime.now().isoformat(), "result": result}
    finally:
        loop.close()


@shared_task(name="tasks.send_daily_hotspot_digest")
def send_daily_hotspot_digest():
    """
    每日热点精选推送
    每晚22:00执行
    """
    print(f"[Celery] 执行每日热点精选: {datetime.now()}")
    
    from app.core.database import async_session_maker
    from app.models.hotspot import HotTopic
    from sqlalchemy import select, desc
    
    async def send_digest():
        async with async_session_maker() as session:
            # 获取今日TOP5热点
            result = await session.execute(
                select(HotTopic)
                .where(HotTopic.status == "active")
                .order_by(desc(HotTopic.heat_score))
                .limit(5)
            )
            topics = result.scalars().all()
            
            # 发送到飞书
            if topics:
                content = "📰 今日热点TOP5\\n\\n"
                for i, topic in enumerate(topics, 1):
                    content += f"{i}. {topic.title} (热度:{topic.heat_score})\\n"
                
                # TODO: 飞书推送
                print(f"[Celery] 每日热点精选:\n{content}")
            return len(topics)
    
    # 创建新的事件循环避免冲突
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        count = loop.run_until_complete(send_digest())
        return {"status": "success", "count": count}
    finally:
        loop.close()


@shared_task(name="tasks.clean_expired_hotspots")
def clean_expired_hotspots():
    """
    清理过期热点
    每天凌晨执行
    """
    print(f"[Celery] 清理过期热点: {datetime.now()}")
    
    from app.services.hotspot_service import hotspot_service
    
    # 创建新的事件循环避免冲突
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(hotspot_service._clean_expired_hotspots())
        return {"status": "success", "result": result}
    finally:
        loop.close()

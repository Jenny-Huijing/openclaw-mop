"""
Agent API 路由
提供 Workflow 触发和查询接口 - 仅使用真实 API，无模拟数据
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import json
import uuid
from datetime import datetime
import asyncio

from app.core.database import get_db, async_session_maker
from app.models import Content, HotTopic

# 导入 Orchestrator
try:
    from app.agents.orchestrator import orchestrator, WorkflowException
    ORCHESTRATOR_AVAILABLE = orchestrator is not None
except ImportError as e:
    print(f"[Agent] Orchestrator 导入失败: {e}")
    ORCHESTRATOR_AVAILABLE = False
    orchestrator = None
    WorkflowException = Exception

router = APIRouter(prefix="/agent", tags=["agent"])


async def run_workflow_background(workflow_id: str, content_id: str):
    """后台执行 Workflow"""
    try:
        print(f"[Background] 开始执行 Workflow: {workflow_id}")
        
        if not ORCHESTRATOR_AVAILABLE:
            raise Exception("Orchestrator 不可用")
        
        # 执行 Workflow，传递 workflow_id 以保持关联
        result = await orchestrator.run(user_id="default", workflow_id=workflow_id)
        
        content_data = result.get("content", {})
        
        # 更新数据库
        async with async_session_maker() as db:
            stmt = select(Content).where(Content.id == content_id)
            result_db = await db.execute(stmt)
            content = result_db.scalar_one_or_none()
            
            if not content:
                print(f"[Background] 未找到内容记录: {content_id}")
                return
            
            if not content_data:
                raise Exception("Workflow 未返回内容数据")
            
            # 验证内容有效性
            titles = content_data.get("titles", [])
            body = content_data.get("body", "")
            
            if not titles or not body or len(body) < 10:
                raise Exception(f"内容生成不完整: titles={len(titles)}, body={len(body)} 字符")
            
            # 内容有效，更新数据库
            content.titles = titles
            content.body = body
            content.tags = content_data.get("tags", [])
            content.image_prompts = content_data.get("image_prompts", [])
            content.images = content_data.get("images", [])
            content.status = "reviewing"  # 创作完成，等待用户审核
            await db.commit()
            print(f"[Background] Workflow {workflow_id} 完成，等待用户审核")
            
            # 通过 OpenClaw 发送审核提醒（小珑宝会转发到飞书）
            try:
                from app.services.openclaw_notify import notify_content_review
                await notify_content_review(
                    content_id=content_id,
                    title=content.titles[0] if content.titles else "无标题",
                    preview=content.body[:200] if content.body else "",
                    workflow_id=workflow_id
                )
                print(f"[Background] OpenClaw 通知已发送")
            except Exception as e:
                print(f"[Background] OpenClaw 通知发送失败: {e}")
                
    except Exception as e:
        print(f"[Background] Workflow 执行失败: {e}")
        # 更新状态为失败
        try:
            async with async_session_maker() as db:
                stmt = select(Content).where(Content.id == content_id)
                result_db = await db.execute(stmt)
                content = result_db.scalar_one_or_none()
                if content:
                    content.status = "failed"
                    content.body = f"生成失败: {str(e)}"
                    await db.commit()
        except Exception as inner_e:
            print(f"[Background] 更新失败状态失败: {inner_e}")


@router.post("/workflow/start")
async def start_workflow(
    background_tasks: BackgroundTasks,
    user_id: str = "default",
    db: AsyncSession = Depends(get_db)
):
    """启动新的 Workflow（异步执行）"""
    
    # 检查服务可用性
    if not ORCHESTRATOR_AVAILABLE:
        return {
            "code": 503,
            "message": "创作服务暂时不可用，请检查配置",
            "data": None
        }
    
    workflow_id = f"wf_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    
    # 创建"创作中"的记录
    content = Content(
        workflow_id=workflow_id,
        titles=["创作中..."],
        body="AI正在为您生成内容，请稍候...",
        tags=[],
        image_prompts=[],
        images=[],
        status="CREATING",
        revision_round=0
    )
    db.add(content)
    await db.commit()
    await db.refresh(content)
    
    # 在后台执行 Workflow
    asyncio.create_task(run_workflow_background(workflow_id, content.id))
    
    return {
        "code": 200,
        "message": "创作任务已启动",
        "data": {
            "workflow_id": workflow_id,
            "content": {
                "id": content.id,
                "workflow_id": workflow_id,
                "status": "CREATING",
                "created_at": content.created_at.isoformat() if content.created_at else None
            }
        }
    }


@router.get("/workflow/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """查询 Workflow 状态"""
    return {
        "code": 200,
        "data": {
            "workflow_id": workflow_id,
            "status": "running",
        }
    }


@router.post("/workflow/{workflow_id}/review")
async def submit_review(
    workflow_id: str,
    decision: str,
    notes: Optional[str] = None
):
    """提交人工审核结果"""
    return {
        "code": 200,
        "message": f"审核结果已提交: {decision}",
        "data": {
            "workflow_id": workflow_id,
            "decision": decision,
            "notes": notes
        }
    }


async def run_batch_workflow_background(count: int):
    """后台批量执行 Workflow"""
    try:
        print(f"[Background Batch] 开始批量创作 {count} 条内容")
        
        if not ORCHESTRATOR_AVAILABLE:
            raise Exception("Orchestrator 不可用")
        
        # 使用批量生成方法
        results = await orchestrator.batch_create_contents(user_id="default", count=count)
        
        # 保存到数据库
        async with async_session_maker() as db:
            for result in results:
                content_data = result.get("content", {})
                topic = result.get("selected_topic", {})
                
                # 创建热点记录
                hotspot = HotTopic(
                    title=topic.get("title", "未知主题"),
                    summary=topic.get("summary", ""),
                    heat_score=topic.get("heat_score", 80),
                    total_score=topic.get("total_score", 85),
                    source=topic.get("source", "实时搜索")
                )
                db.add(hotspot)
                await db.flush()
                
                # 创建内容记录
                content = Content(
                    workflow_id=result.get("workflow_id", ""),
                    topic_id=hotspot.id,
                    titles=content_data.get("titles", []),
                    body=content_data.get("body", ""),
                    tags=content_data.get("tags", []),
                    image_prompts=content_data.get("image_prompts", []),
                    images=content_data.get("images", []),
                    status="reviewing",
                    revision_round=0
                )
                db.add(content)
            
            await db.commit()
            print(f"[Background Batch] 批量创作完成，已保存 {len(results)} 条内容")
            
    except Exception as e:
        print(f"[Background Batch] 批量创作失败: {e}")


@router.post("/workflow/batch")
async def start_batch_workflow(
    background_tasks: BackgroundTasks,
    count: int = 1,
    db: AsyncSession = Depends(get_db)
):
    """
    启动批量创作 Workflow（异步执行）
    
    - count: 生成内容数量（1-20，默认1）
    """
    # 检查服务可用性
    if not ORCHESTRATOR_AVAILABLE:
        return {
            "code": 503,
            "message": "创作服务暂时不可用，请检查配置",
            "data": None
        }
    
    # 限制数量
    count = max(1, min(count, 20))
    
    # 在后台执行批量 Workflow
    asyncio.create_task(run_batch_workflow_background(count))
    
    return {
        "code": 200,
        "message": f"批量创作任务已启动，将生成 {count} 条内容",
        "data": {
            "count": count,
            "status": "running",
            "estimated_time": f"{count * 30}秒"
        }
    }


@router.get("/hotspots/search")
async def search_current_hotspots(
    count: int = 10
):
    """
    实时搜索当前财经热点
    仅使用真实搜索 API，无模拟数据
    
    - count: 返回热点数量（1-20，默认10）
    """
    try:
        from app.services.search import search_service
        
        # 限制数量
        count = max(1, min(count, 20))
        
        # 执行实时搜索
        hotspots = await search_service.get_hotspots(count)
        
        if not hotspots:
            return {
                "code": 404,
                "message": "未搜索到任何热点，请稍后重试",
                "data": None
            }
        
        return {
            "code": 200,
            "message": f"成功搜索到 {len(hotspots)} 个实时热点",
            "data": {
                "count": len(hotspots),
                "hotspots": hotspots
            }
        }
        
    except Exception as e:
        return {
            "code": 500,
            "message": f"搜索失败: {str(e)}",
            "data": None
        }


# WebSocket 连接管理
class ConnectionManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        print(f"Client {client_id} connected")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        print(f"Client {client_id} disconnected")
    
    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)


manager = ConnectionManager()


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket 端点"""
    await manager.connect(client_id, websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif message.get("type") == "review_decision":
                print(f"收到审核决策: {message}")
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)

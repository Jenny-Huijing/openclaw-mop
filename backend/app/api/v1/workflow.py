"""
工作流 API
"""

from typing import Optional
from fastapi import APIRouter, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.core.database import get_db
from app.models import WorkflowLog
from app.schemas import ApiResponse

router = APIRouter(prefix="/workflow", tags=["workflow"])


@router.get("/graph", response_model=ApiResponse)
async def get_workflow_graph():
    """获取工作流 Mermaid 图"""
    try:
        from app.agents.orchestrator import OrchestratorAgent, LANGGRAPH_AVAILABLE
        
        if not LANGGRAPH_AVAILABLE:
            return ApiResponse(
                code=503,
                message="LangGraph 不可用"
            )
        
        # 创建 orchestrator 实例获取 graph
        agent = OrchestratorAgent()
        
        # 获取 Mermaid 图
        mermaid_code = agent.get_workflow_graph()
        
        return ApiResponse(
            data={
                "mermaid": mermaid_code,
                "type": "mermaid"
            }
        )
    except Exception as e:
        return ApiResponse(
            code=500,
            message=f"获取工作流图失败: {str(e)}"
        )


@router.get("/logs", response_model=ApiResponse)
async def get_workflow_logs(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """获取工作流执行日志"""
    try:
        result = await db.execute(
            select(WorkflowLog)
            .order_by(desc(WorkflowLog.created_at))
            .offset(offset)
            .limit(limit)
        )
        logs = result.scalars().all()
        
        return ApiResponse(
            data={
                "items": [log.to_dict() for log in logs],
                "total": len(logs)
            }
        )
    except Exception as e:
        return ApiResponse(
            code=500,
            message=f"获取工作流日志失败: {str(e)}"
        )


@router.get("/status", response_model=ApiResponse)
async def get_workflow_status(
    db: AsyncSession = Depends(get_db)
):
    """获取当前工作流状态统计"""
    try:
        # 统计各状态的数量
        from sqlalchemy import func
        
        result = await db.execute(
            select(WorkflowLog.status, func.count(WorkflowLog.id))
            .group_by(WorkflowLog.status)
        )
        status_counts = dict(result.all())
        
        # 最近24小时的活动
        from datetime import datetime, timedelta
        yesterday = datetime.now() - timedelta(days=1)
        
        recent_result = await db.execute(
            select(func.count(WorkflowLog.id))
            .where(WorkflowLog.created_at >= yesterday)
        )
        recent_count = recent_result.scalar()
        
        return ApiResponse(
            data={
                "status_counts": status_counts,
                "recent_24h": recent_count,
                "is_running": True  # 工作流始终运行
            }
        )
    except Exception as e:
        return ApiResponse(
            code=500,
            message=f"获取工作流状态失败: {str(e)}"
        )

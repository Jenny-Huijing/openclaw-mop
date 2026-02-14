"""
API路由聚合
"""

from fastapi import APIRouter

from app.api.v1 import task, content, hotspot, stats, agent, xhs, publish, log, workflow, scheduler
from app.agents.hotspot_agent import router as hotspot_agent_router

api_router = APIRouter(prefix="/api/v1")

# 注册路由
api_router.include_router(task.router)
api_router.include_router(content.router)
api_router.include_router(hotspot.router)
api_router.include_router(stats.router)
api_router.include_router(agent.router)
api_router.include_router(xhs.router)
api_router.include_router(publish.router)
api_router.include_router(log.router)
api_router.include_router(workflow.router)
api_router.include_router(scheduler.router)
api_router.include_router(hotspot_agent_router)

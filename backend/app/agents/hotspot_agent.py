"""
热点获取 Agent - LangGraph 实现
可独立运行、可配置、支持多数据源的热点获取系统
"""

from typing import TypedDict, Annotated, List, Dict, Optional
from datetime import datetime
import asyncio
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
import json
import re
from difflib import SequenceMatcher

from app.models.v4_models import HotTopic, HotTopicTrend
from app.core.database import async_session_maker
from app.services.search import search_service


class HotspotState(TypedDict):
    """热点获取 Agent 状态"""
    # 配置参数
    keywords: List[str]              # 搜索关键词
    categories: List[str]            # 关注的分类
    sources: List[str]               # 数据源列表
    min_heat_score: int              # 最小热度分
    max_results: int                 # 最大结果数
    
    # 执行状态
    raw_hotspots: List[Dict]         # 原始热点数据
    processed_hotspots: List[Dict]   # 处理后的热点
    errors: List[str]                # 错误日志
    
    # 结果
    new_hotspots: int                # 新增热点数
    updated_hotspots: int            # 更新热点数
    saved_ids: List[str]             # 保存的热点ID


class HotspotFetcherAgent:
    """热点获取 Agent"""
    
    # 支持的数据源
    SOURCES = {
        "brave_search": "Brave Search API - 财经热点",
        "weibo": "微博热搜",
        "baidu": "百度热搜",
        "zhihu": "知乎热榜",
        "toutiao": "头条热搜",
        "custom_search": "自定义搜索"
    }
    
    # 分类关键词配置
    CATEGORIES = {
        "finance": {
            "name": "财经",
            "keywords": ["降息", "加息", "股市", "基金", "理财", "银行", "保险", "投资", "经济", "财经", "LPR", "存款", "国债", "黄金", "汇率"],
            "weight": 1.5
        },
        "tech": {
            "name": "科技",
            "keywords": ["AI", "人工智能", "芯片", "科技", "互联网", "手机", "电动车", "新能源", "5G", "区块链"],
            "weight": 1.3
        },
        "lifestyle": {
            "name": "生活",
            "keywords": ["生活", "美食", "旅游", "家居", "穿搭", "护肤", "健身", "养生", "健康"],
            "weight": 1.0
        },
        "social": {
            "name": "社会",
            "keywords": ["社会", "民生", "教育", "医疗", "就业", "房价", "养老", "政策", "交通"],
            "weight": 1.2
        },
        "entertainment": {
            "name": "娱乐",
            "keywords": ["明星", "综艺", "电影", "电视剧", "音乐", "娱乐", "八卦", "直播"],
            "weight": 0.8
        }
    }
    
    def __init__(self):
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """构建 LangGraph 工作流"""
        
        workflow = StateGraph(HotspotState)
        
        # 定义节点
        workflow.add_node("fetch_brave", self.fetch_from_brave)
        workflow.add_node("fetch_trending", self.fetch_trending_platforms)
        workflow.add_node("merge_results", self.merge_hotspots)
        workflow.add_node("classify", self.classify_hotspots)
        workflow.add_node("save_to_db", self.save_to_database)
        workflow.add_node("log_summary", self.log_summary)
        
        # 定义边
        workflow.set_entry_point("fetch_brave")
        
        # 并行获取数据
        workflow.add_edge("fetch_brave", "fetch_trending")
        workflow.add_edge("fetch_trending", "merge_results")
        
        # 处理数据
        workflow.add_edge("merge_results", "classify")
        workflow.add_edge("classify", "save_to_db")
        workflow.add_edge("save_to_db", "log_summary")
        workflow.add_edge("log_summary", END)
        
        return workflow.compile()
    
    async def fetch_from_brave(self, state: HotspotState) -> HotspotState:
        """从 Brave Search 获取热点"""
        if "brave_search" not in state["sources"]:
            return state
        
        hotspots = []
        keywords = state.get("keywords", ["财经热点", "投资理财", "股市动态"])
        
        for keyword in keywords[:3]:  # 限制关键词数量
            try:
                results = await search_service.search_brave(
                    query=keyword,
                    count=state.get("max_results", 10) // 3
                )
                
                for item in results:
                    hotspots.append({
                        "title": item.get("title", ""),
                        "summary": item.get("description", ""),
                        "heat_score": item.get("score", 50),
                        "source": "brave_search",
                        "source_url": item.get("url", ""),
                        "keywords": [],
                        "fetched_at": datetime.now().isoformat()
                    })
                    
            except Exception as e:
                state["errors"].append(f"Brave Search [{keyword}]: {str(e)}")
        
        state["raw_hotspots"].extend(hotspots)
        return state
    
    async def fetch_trending_platforms(self, state: HotspotState) -> HotspotState:
        """从各平台热搜获取数据"""
        from app.services.trending_platform import trending_service
        
        hotspots = []
        sources = state.get("sources", [])
        
        # 获取多平台数据
        try:
            platform_data = await trending_service.fetch_all_trending()
            
            for platform, items in platform_data.items():
                if platform not in sources:
                    continue
                
                for item in items[:10]:  # 每个平台取前10
                    hotspots.append({
                        "title": item.get("title", ""),
                        "summary": f"{platform}热搜榜第{item.get('rank', 0)}名",
                        "heat_score": item.get("score", 50),
                        "source": platform,
                        "source_url": item.get("url", ""),
                        "keywords": [],
                        "fetched_at": datetime.now().isoformat()
                    })
                    
        except Exception as e:
            state["errors"].append(f"Trending platforms: {str(e)}")
        
        state["raw_hotspots"].extend(hotspots)
        return state
    
    async def merge_hotspots(self, state: HotspotState) -> HotspotState:
        """合并并去重热点"""
        raw = state["raw_hotspots"]
        merged = []
        seen_titles = set()
        
        for hotspot in raw:
            title = hotspot["title"].strip()
            if not title:
                continue
            
            # 检查是否已存在相似标题
            is_duplicate = False
            for seen_title in seen_titles:
                similarity = SequenceMatcher(None, title.lower(), seen_title.lower()).ratio()
                if similarity > 0.7:  # 70% 相似度视为重复
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen_titles.add(title)
                merged.append(hotspot)
        
        # 按热度排序
        merged.sort(key=lambda x: x.get("heat_score", 0), reverse=True)
        
        # 限制结果数
        state["processed_hotspots"] = merged[:state.get("max_results", 20)]
        return state
    
    async def classify_hotspots(self, state: HotspotState) -> HotspotState:
        """对热点进行分类"""
        categories_filter = state.get("categories", [])
        
        for hotspot in state["processed_hotspots"]:
            text = (hotspot.get("title", "") + " " + hotspot.get("summary", "")).lower()
            
            # 计算各分类得分
            scores = {}
            for key, config in self.CATEGORIES.items():
                if categories_filter and key not in categories_filter:
                    continue
                
                score = 0
                for keyword in config["keywords"]:
                    if keyword.lower() in text:
                        score += 1
                scores[key] = score * config["weight"]
            
            # 选择得分最高的分类
            if scores and max(scores.values()) > 0:
                best_category = max(scores, key=scores.get)
                hotspot["category"] = best_category
            else:
                hotspot["category"] = "other"
        
        return state
    
    async def save_to_database(self, state: HotspotState) -> HotspotState:
        """保存到数据库"""
        new_count = 0
        updated_count = 0
        saved_ids = []
        
        async with async_session_maker() as session:
            for hotspot in state["processed_hotspots"]:
                try:
                    # 检查是否已存在相似热点
                    existing = await self._find_similar_topic(
                        session, 
                        hotspot["title"]
                    )
                    
                    if existing:
                        # 更新现有热点
                        await self._update_topic(session, existing, hotspot)
                        updated_count += 1
                        saved_ids.append(existing.id)
                    else:
                        # 创建新热点
                        new_topic = await self._create_topic(session, hotspot)
                        new_count += 1
                        saved_ids.append(new_topic.id)
                        
                except Exception as e:
                    state["errors"].append(f"Save [{hotspot.get('title', 'unknown')}]: {str(e)}")
            
            await session.commit()
        
        state["new_hotspots"] = new_count
        state["updated_hotspots"] = updated_count
        state["saved_ids"] = saved_ids
        return state
    
    async def _find_similar_topic(self, session: AsyncSession, title: str) -> Optional[HotTopic]:
        """查找相似标题的热点"""
        from sqlalchemy import select, desc
        from datetime import timedelta
        
        three_days_ago = datetime.utcnow() - timedelta(days=3)
        
        result = await session.execute(
            select(HotTopic)
            .where(HotTopic.discovered_at >= three_days_ago)
            .where(HotTopic.status != "expired")
            .order_by(desc(HotTopic.discovered_at))
        )
        
        for topic in result.scalars().all():
            similarity = SequenceMatcher(None, topic.title, title).ratio()
            if similarity > 0.8:
                return topic
        
        return None
    
    async def _update_topic(self, session: AsyncSession, topic: HotTopic, data: Dict):
        """更新现有热点"""
        old_heat = topic.heat_score
        new_heat = data.get("heat_score", 0)
        
        topic.heat_score = max(old_heat, new_heat)
        topic.updated_at = datetime.utcnow()
        
        # 记录趋势
        trend = HotTopicTrend(
            id=str(uuid.uuid4()),
            topic_id=topic.id,
            heat_score=new_heat,
            recorded_at=datetime.utcnow()
        )
        session.add(trend)
    
    async def _create_topic(self, session: AsyncSession, data: Dict) -> HotTopic:
        """创建新热点"""
        import uuid
        from datetime import timedelta
        
        topic = HotTopic(
            id=str(uuid.uuid4()),
            title=data["title"],
            summary=data.get("summary", ""),
            heat_score=data.get("heat_score", 50),
            trend="stable",
            category=data.get("category", "other"),
            source=data.get("source", "unknown"),
            source_url=data.get("source_url", ""),
            keywords=data.get("keywords", []),
            discovered_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=3),
        )
        session.add(topic)
        
        # 记录初始趋势
        trend = HotTopicTrend(
            id=str(uuid.uuid4()),
            topic_id=topic.id,
            heat_score=topic.heat_score,
            recorded_at=datetime.utcnow()
        )
        session.add(trend)
        
        return topic
    
    async def log_summary(self, state: HotspotState) -> HotspotState:
        """记录执行摘要"""
        summary = f"""
[HotspotAgent] 执行完成
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
配置参数:
  - 数据源: {state.get('sources', [])}
  - 关键词: {state.get('keywords', [])}
  - 分类: {state.get('categories', [])}

执行结果:
  - 抓取热点: {len(state.get('raw_hotspots', []))} 条
  - 去重后: {len(state.get('processed_hotspots', []))} 条
  - 新增: {state.get('new_hotspots', 0)} 条
  - 更新: {state.get('updated_hotspots', 0)} 条

错误记录: {len(state.get('errors', []))} 条
"""
        if state.get('errors'):
            summary += f"\n错误详情:\n" + "\n".join(f"  - {e}" for e in state['errors'][:5])
        
        print(summary)
        return state
    
    # ============ 公共接口 ============
    
    async def run(
        self,
        keywords: List[str] = None,
        categories: List[str] = None,
        sources: List[str] = None,
        min_heat_score: int = 50,
        max_results: int = 20
    ) -> Dict:
        """
        执行热点获取任务
        
        示例:
            agent = HotspotFetcherAgent()
            result = await agent.run(
                keywords=["财经", "投资"],
                categories=["finance", "tech"],
                sources=["brave_search", "weibo", "baidu"],
                max_results=10
            )
        """
        
        initial_state: HotspotState = {
            "keywords": keywords or ["财经热点", "投资理财"],
            "categories": categories or ["finance", "tech", "social"],
            "sources": sources or ["brave_search", "weibo", "baidu", "zhihu"],
            "min_heat_score": min_heat_score,
            "max_results": max_results,
            "raw_hotspots": [],
            "processed_hotspots": [],
            "errors": [],
            "new_hotspots": 0,
            "updated_hotspots": 0,
            "saved_ids": []
        }
        
        result = await self.graph.ainvoke(initial_state)
        return {
            "total_fetched": len(result["raw_hotspots"]),
            "unique_hotspots": len(result["processed_hotspots"]),
            "new_hotspots": result["new_hotspots"],
            "updated_hotspots": result["updated_hotspots"],
            "saved_ids": result["saved_ids"],
            "errors": result["errors"]
        }
    
    async def run_scheduled(
        self,
        schedule_config: Dict = None
    ) -> Dict:
        """
        定时执行配置
        
        默认配置:
            - 每小时执行一次
            - 抓取财经、科技、社会类热点
            - 最大20条结果
        """
        config = schedule_config or {
            "keywords": ["财经", "理财", "投资", "股市", "基金"],
            "categories": ["finance", "tech", "social"],
            "sources": ["brave_search", "weibo", "baidu"],
            "max_results": 20
        }
        
        return await self.run(**config)


# 全局 Agent 实例
hotspot_agent = HotspotFetcherAgent()


# ============ Celery 定时任务 ============

from app.tasks.celery_app import celery_app

@celery_app.task(name="tasks.fetch_hotspots_v2")
def fetch_hotspots_v2_task():
    """
    新版热点抓取任务 - 使用 LangGraph Agent
    每2小时执行一次
    """
    import asyncio
    
    async def run():
        agent = HotspotFetcherAgent()
        result = await agent.run_scheduled()
        return result
    
    return asyncio.run(run())


@celery_app.task(name="tasks.fetch_hotspots_custom")
def fetch_hotspots_custom_task(
    keywords: List[str] = None,
    categories: List[str] = None,
    max_results: int = 10
):
    """
    自定义热点抓取任务
    可指定关键词、分类等参数
    """
    import asyncio
    
    async def run():
        agent = HotspotFetcherAgent()
        result = await agent.run(
            keywords=keywords,
            categories=categories,
            max_results=max_results
        )
        return result
    
    return asyncio.run(run())


# ============ API 接口 ============

from fastapi import APIRouter, Query
from typing import List, Optional
from app.schemas import ApiResponse

router = APIRouter(prefix="/agent/hotspots", tags=["热点Agent"])

@router.post("/fetch", response_model=ApiResponse)
async def fetch_hotspots_with_agent(
    keywords: Optional[List[str]] = Query(None, description="搜索关键词"),
    categories: Optional[List[str]] = Query(None, description="分类筛选"),
    sources: Optional[List[str]] = Query(None, description="数据源"),
    max_results: int = Query(20, ge=1, le=50, description="最大结果数")
):
    """
    使用 Agent 抓取热点
    
    示例:
        POST /api/v1/agent/hotspots/fetch?keywords=财经&keywords=投资&max_results=10
    """
    try:
        agent = HotspotFetcherAgent()
        result = await agent.run(
            keywords=keywords,
            categories=categories,
            sources=sources,
            max_results=max_results
        )
        
        return ApiResponse(
            message="热点抓取完成",
            data=result
        )
    except Exception as e:
        import traceback
        return ApiResponse(
            code=500,
            message=f"抓取失败: {str(e)}"
        )


@router.post("/fetch/scheduled", response_model=ApiResponse)
async def trigger_scheduled_fetch():
    """触发定时抓取任务"""
    from celery import chain
    
    # 异步执行
    fetch_hotspots_v2_task.delay()
    
    return ApiResponse(message="定时抓取任务已触发")

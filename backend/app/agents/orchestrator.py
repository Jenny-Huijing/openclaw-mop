"""
Orchestrator Agent - Workflow 总调度
基于 LangGraph 状态图编排

注意：本模块不包含任何模拟数据，所有数据必须来自真实 API
"""

from typing import TypedDict, Optional, List
from datetime import datetime
import uuid
import random
import asyncio

# LangGraph
try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    StateGraph = None
    END = None

# LLM 服务
try:
    from app.services.llm import llm_service, LLMServiceException, get_llm_service
    from app.services.image import image_service
    from app.services.search import search_service
    LLM_AVAILABLE = llm_service is not None
    IMAGE_AVAILABLE = image_service is not None
    SEARCH_AVAILABLE = search_service is not None
except ImportError as e:
    print(f"[Orchestrator] 服务导入失败: {e}")
    LLM_AVAILABLE = False
    IMAGE_AVAILABLE = False
    SEARCH_AVAILABLE = False
    llm_service = None
    image_service = None
    search_service = None
    get_llm_service = None


class WorkflowException(Exception):
    """Workflow 异常"""
    pass


class WorkflowState(TypedDict):
    """Workflow 状态定义"""
    workflow_id: str
    user_id: str
    hot_topics: List[dict]
    selected_topic: Optional[dict]
    content: Optional[dict]
    compliance_result: Optional[dict]
    review_decision: Optional[str]
    revision_notes: Optional[str]
    revision_round: int
    published: bool
    error: Optional[str]
    recent_topics: Optional[List[str]]


class OrchestratorAgent:
    """
    Workflow 总调度 Agent
    注意：所有数据来自真实 API，无模拟数据
    """
    
    def __init__(self):
        if not LANGGRAPH_AVAILABLE:
            raise WorkflowException("LangGraph 不可用，无法初始化 Orchestrator")
        
        if not SEARCH_AVAILABLE:
            raise WorkflowException("搜索服务不可用，无法初始化 Orchestrator")
        
        if not LLM_AVAILABLE:
            raise WorkflowException("LLM 服务不可用，无法初始化 Orchestrator")
        
        self.workflow = self._build_workflow()
    
    def _build_workflow(self):
        """构建 LangGraph 状态图"""
        
        workflow = StateGraph(WorkflowState)
        
        # 添加节点（Agent）
        workflow.add_node("research", self.research_node)
        workflow.add_node("compliance_check", self.compliance_check_node)
        workflow.add_node("create", self.create_node)
        workflow.add_node("compliance_review", self.compliance_review_node)
        workflow.add_node("review", self.human_review_node)
        workflow.add_node("publish", self.publish_node)
        workflow.add_node("analytics", self.analytics_node)
        
        # 定义边（流转逻辑）
        workflow.set_entry_point("research")
        workflow.add_edge("research", "compliance_check")
        
        # 热点合规检查后决策
        workflow.add_conditional_edges(
            "compliance_check",
            self._route_compliance_check,
            {
                "create": "create",
                "end": END
            }
        )
        
        workflow.add_edge("create", "compliance_review")
        
        # 内容合规审查后决策
        workflow.add_conditional_edges(
            "compliance_review",
            self._route_compliance_review,
            {
                "review": "review",
                "end": END
            }
        )
        
        # 人工审核后决策
        workflow.add_conditional_edges(
            "review",
            self._route_review_decision,
            {
                "publish": "publish",
                "create": "create",
                "end": END
            }
        )
        
        workflow.add_edge("publish", "analytics")
        workflow.add_edge("analytics", END)
        
        return workflow.compile()
    
    def _route_compliance_check(self, state: WorkflowState) -> str:
        """热点合规检查后路由"""
        result = state.get("compliance_result", {})
        if result.get("status") == "BLOCK":
            return "end"
        return "create"
    
    def _route_compliance_review(self, state: WorkflowState) -> str:
        """内容合规审查后路由"""
        result = state.get("compliance_result", {})
        if result.get("status") == "BLOCK":
            # 合规检查失败，保存内容到数据库，等待用户处理
            return "review"  # 改为进入审核阶段，让用户看到合规问题
        return "review"
    
    def _route_review_decision(self, state: WorkflowState) -> str:
        """人工审核后路由"""
        decision = state.get("review_decision")
        
        # 如果决策为 None，表示等待用户审核，工作流结束
        if decision is None:
            return "end"
        
        if decision == "approved":
            return "publish"
        elif decision == "revision":
            if state.get("revision_round", 0) < 3:
                return "create"
            else:
                return "end"
        else:
            return "end"
    
    async def research_node(self, state: WorkflowState) -> WorkflowState:
        """
        Research Agent: 热点发现
        仅使用实时搜索，无备用数据
        """
        from app.core.database import async_session_maker
        from app.models.v4_models import WorkflowLog
        import time
        
        start_time = time.time()
        workflow_id = state['workflow_id']
        print(f"[{workflow_id}] Research Agent: 开始实时搜索热点...")
        
        # 记录开始
        async with async_session_maker() as session:
            log = WorkflowLog(
                id=str(uuid.uuid4()),
                workflow_id=workflow_id,
                agent_name="Research Agent",
                action="开始实时搜索热点",
                status="RUNNING",
                input_data={"recent_topics": state.get("recent_topics", [])},
                created_at=datetime.now()
            )
            session.add(log)
            await session.commit()
        
        try:
            # 调用实时搜索 API
            search_results = await search_service.get_hotspots(count=15)
            
            if not search_results:
                raise WorkflowException("实时搜索未返回任何热点")
            
            # 过滤掉最近使用过的热点
            recent_topics = state.get("recent_topics", [])
            hot_topics = [h for h in search_results if h["title"] not in recent_topics]
            
            if not hot_topics:
                # 如果都用过，重新使用所有热点
                hot_topics = search_results
            
            # 按综合评分排序
            hot_topics.sort(key=lambda x: x.get("total_score", 0), reverse=True)
            hot_topics = hot_topics[:5]
            
            # 随机选择一个热点
            selected_topic = random.choice(hot_topics)
            
            state["hot_topics"] = hot_topics
            state["selected_topic"] = selected_topic
            
            duration_ms = int((time.time() - start_time) * 1000)
            print(f"[{workflow_id}] Research Agent: 发现 {len(hot_topics)} 个热点")
            print(f"[{workflow_id}] 选中主题: {selected_topic['title']}")
            print(f"[{workflow_id}] 来源: {selected_topic.get('source', '未知')}")
            
            # 记录成功
            async with async_session_maker() as session:
                log = WorkflowLog(
                    id=str(uuid.uuid4()),
                    workflow_id=workflow_id,
                    agent_name="Research Agent",
                    action="热点搜索完成",
                    status="SUCCESS",
                    output_data={
                        "hot_topics_count": len(hot_topics),
                        "selected_topic": selected_topic['title'],
                        "source": selected_topic.get('source', '未知')
                    },
                    duration_ms=duration_ms,
                    created_at=datetime.now()
                )
                session.add(log)
                await session.commit()
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            print(f"[{workflow_id}] Research Agent: 搜索失败 - {e}")
            
            # 记录失败
            async with async_session_maker() as session:
                log = WorkflowLog(
                    id=str(uuid.uuid4()),
                    workflow_id=workflow_id,
                    agent_name="Research Agent",
                    action="热点搜索失败",
                    status="FAILED",
                    error_message=str(e),
                    duration_ms=duration_ms,
                    created_at=datetime.now()
                )
                session.add(log)
                await session.commit()
            
            raise WorkflowException(f"热点搜索失败: {str(e)}")
        
        return state
    
    async def _create_single_content(self, index: int, count: int, user_id: str, recent_topics: list) -> dict:
        """创建单条内容（用于并行批量创作）"""
        print(f"\n--- 第 {index+1}/{count} 条内容 ---")
        
        workflow_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{index+1}"
        
        initial_state: WorkflowState = {
            "workflow_id": workflow_id,
            "user_id": user_id,
            "hot_topics": [],
            "selected_topic": None,
            "content": None,
            "compliance_result": None,
            "review_decision": None,
            "revision_notes": None,
            "revision_round": 0,
            "published": False,
            "error": None,
            "recent_topics": recent_topics.copy()  # 复制列表避免竞争
        }
        
        try:
            result = await self.workflow.ainvoke(initial_state)
            
            if result.get("content"):
                topic_title = result.get("selected_topic", {}).get("title", "未知主题")
                print(f"✅ 第 {index+1} 条完成: {topic_title[:30]}...")
                return {
                    "result": result,
                    "topic_title": topic_title,
                    "success": True
                }
            else:
                raise WorkflowException("内容生成失败，未返回有效内容")
                
        except Exception as e:
            print(f"❌ 第 {index+1} 条内容生成失败: {e}")
            raise WorkflowException(f"批量创作第 {index+1} 条失败: {str(e)}")
    
    async def batch_create_contents(self, user_id: str = "default", count: int = 10) -> list:
        """
        批量生成内容（并行执行）
        注意：如果任何一步失败，会直接抛出异常，不会返回假数据
        """
        print(f"\n{'='*60}")
        print(f"🚀 批量创作模式（并行）: 生成 {count} 条内容")
        print(f"{'='*60}\n")
        
        results = []
        recent_topics = []
        
        # 并行创建所有内容
        tasks = [
            self._create_single_content(i, count, user_id, recent_topics)
            for i in range(count)
        ]
        
        # 使用 gather 并行执行，return_exceptions=True 捕获异常
        completed_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        for i, item in enumerate(completed_results):
            if isinstance(item, Exception):
                print(f"❌ 第 {i+1} 条内容生成失败: {item}")
                raise WorkflowException(f"批量创作第 {i+1} 条失败: {str(item)}")
            elif item.get("success"):
                results.append(item["result"])
                recent_topics.append(item["topic_title"])
        
        print(f"\n{'='*60}")
        print(f"✅ 批量创作完成: {len(results)}/{count} 条成功")
        print(f"{'='*60}\n")
        
        return results
    
    async def compliance_check_node(self, state: WorkflowState) -> WorkflowState:
        """Compliance Agent: 热点合规检查"""
        from app.core.database import async_session_maker
        from app.models.v4_models import WorkflowLog
        import time
        
        start_time = time.time()
        workflow_id = state['workflow_id']
        print(f"[{workflow_id}] Compliance Agent: 检查热点合规性...")
        
        # 记录开始
        async with async_session_maker() as session:
            log = WorkflowLog(
                id=str(uuid.uuid4()),
                workflow_id=workflow_id,
                agent_name="Compliance Agent",
                action="检查热点合规性",
                status="RUNNING",
                input_data={"topic_title": state.get("selected_topic", {}).get("title", "")},
                created_at=datetime.now()
            )
            session.add(log)
            await session.commit()
        
        topic = state.get("selected_topic", {})
        title = topic.get("title", "")
        
        # 简单关键词检查
        blacklist = ["政治", "敏感", "非法", "暴恐", "色情"]
        is_safe = not any(word in title for word in blacklist)
        
        result = {
            "status": "PASS" if is_safe else "BLOCK",
            "risk_level": "LOW" if is_safe else "HIGH",
            "issues": [] if is_safe else ["包含敏感词"],
            "suggestions": []
        }
        
        state["compliance_result"] = result
        
        # 记录完成
        duration_ms = int((time.time() - start_time) * 1000)
        async with async_session_maker() as session:
            log = WorkflowLog(
                id=str(uuid.uuid4()),
                workflow_id=workflow_id,
                agent_name="Compliance Agent",
                action="合规检查完成",
                status="SUCCESS" if is_safe else "BLOCKED",
                output_data=result,
                duration_ms=duration_ms,
                created_at=datetime.now()
            )
            session.add(log)
            await session.commit()
        
        print(f"[{workflow_id}] Compliance Agent: 检查结果 {result['status']}")
        return state
    
    async def create_node(self, state: WorkflowState) -> WorkflowState:
        """
        Creator Agent: 内容创作
        仅使用真实 LLM API，无模拟数据
        """
        from app.core.database import async_session_maker
        from app.models.v4_models import WorkflowLog
        import time
        
        start_time = time.time()
        workflow_id = state['workflow_id']
        print(f"[{workflow_id}] Creator Agent: 开始创作内容...")
        
        # 记录开始
        async with async_session_maker() as session:
            log = WorkflowLog(
                id=str(uuid.uuid4()),
                workflow_id=workflow_id,
                agent_name="Creator Agent",
                action="开始内容创作",
                status="RUNNING",
                input_data={"topic": state.get("selected_topic", {}).get("title", "")},
                created_at=datetime.now()
            )
            session.add(log)
            await session.commit()
        
        topic = state.get("selected_topic", {})
        
        try:
            # 获取 LLM 服务实例
            if get_llm_service:
                llm = get_llm_service()
            else:
                raise WorkflowException("LLM 服务不可用")
            
            # 调用 LLM 生成内容（带90秒超时）
            print(f"[{state['workflow_id']}] 调用大模型生成内容...")
            import asyncio
            try:
                llm_result = await asyncio.wait_for(
                    llm.generate_content(topic),
                    timeout=90.0
                )
            except asyncio.TimeoutError:
                raise WorkflowException("LLM 生成内容超时（90秒），请检查网络或稍后重试")
            
            content = {
                "id": str(uuid.uuid4()),
                "workflow_id": state["workflow_id"],
                "titles": llm_result.get("titles", []),
                "body": llm_result.get("body", ""),
                "tags": llm_result.get("tags", []),
                "image_prompts": llm_result.get("image_prompts", [])
            }
            
            # 验证内容有效性 - 必须有标题和正文
            if not content["titles"] or not content["body"] or len(content["body"]) < 10:
                raise WorkflowException(f"内容生成失败: 返回的内容不完整 (titles: {len(content['titles'])}, body: {len(content['body'])} 字符)")
            
            # 生成配图（可选，失败不影响主流程）
            if (IMAGE_AVAILABLE and image_service and image_service.enabled 
                and content["image_prompts"]):
                print(f"[{state['workflow_id']}] 开始生成配图...")
                try:
                    images = await image_service.generate_images(
                        prompts=content["image_prompts"][:2],
                        content_id=content["id"]
                    )
                    content["images"] = images
                    print(f"[{state['workflow_id']}] 配图生成完成: {len(images)} 张")
                except Exception as e:
                    print(f"[{state['workflow_id']}] 配图生成失败: {e}")
                    content["images"] = []
            
            duration_ms = int((time.time() - start_time) * 1000)
            print(f"[{workflow_id}] 大模型内容生成完成")
            
            # 记录成功
            async with async_session_maker() as session:
                log = WorkflowLog(
                    id=str(uuid.uuid4()),
                    workflow_id=workflow_id,
                    agent_name="Creator Agent",
                    action="内容创作完成",
                    status="SUCCESS",
                    output_data={
                        "titles": content.get("titles", []),
                        "body_length": len(content.get("body", "")),
                        "tags": content.get("tags", []),
                        "images_count": len(content.get("images", []))
                    },
                    duration_ms=duration_ms,
                    created_at=datetime.now()
                )
                session.add(log)
                await session.commit()
            
        except LLMServiceException as e:
            duration_ms = int((time.time() - start_time) * 1000)
            print(f"[{workflow_id}] LLM 服务错误: {e}")
            
            # 记录失败
            async with async_session_maker() as session:
                log = WorkflowLog(
                    id=str(uuid.uuid4()),
                    workflow_id=workflow_id,
                    agent_name="Creator Agent",
                    action="内容创作失败",
                    status="FAILED",
                    error_message=str(e),
                    duration_ms=duration_ms,
                    created_at=datetime.now()
                )
                session.add(log)
                await session.commit()
            
            raise WorkflowException(f"内容创作失败: {str(e)}")
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            print(f"[{workflow_id}] 内容创作异常: {e}")
            
            # 记录失败
            async with async_session_maker() as session:
                log = WorkflowLog(
                    id=str(uuid.uuid4()),
                    workflow_id=workflow_id,
                    agent_name="Creator Agent",
                    action="内容创作异常",
                    status="FAILED",
                    error_message=str(e),
                    duration_ms=duration_ms,
                    created_at=datetime.now()
                )
                session.add(log)
                await session.commit()
            
            raise WorkflowException(f"内容创作失败: {str(e)}")
        
        state["content"] = content
        state["revision_round"] = state.get("revision_round", 0) + 1
        
        print(f"[{workflow_id}] Creator Agent: 内容生成完成")
        return state
    
    async def compliance_review_node(self, state: WorkflowState) -> WorkflowState:
        """Compliance Agent: 内容合规审查"""
        from app.core.database import async_session_maker
        from app.models.v4_models import WorkflowLog
        from app.models import Content
        import time
        
        start_time = time.time()
        workflow_id = state['workflow_id']
        print(f"[{workflow_id}] Compliance Agent: 审查内容合规性...")
        
        content_data = state.get("content", {})
        body = content_data.get("body", "")
        titles = content_data.get("titles", [])
        
        # 进行合规检查
        issues = []
        suggestions = []
        
        # 检查敏感词
        blacklist = ["政治", "敏感", "非法", "暴恐", "色情", "赌博", "毒品"]
        for word in blacklist:
            if word in body or any(word in t for t in titles):
                issues.append(f"包含敏感词: {word}")
        
        # 检查正文长度
        if len(body) < 50:
            issues.append("正文过短，建议增加内容")
        
        # 检查是否包含免责声明
        if "理财有风险" not in body and "投资需谨慎" not in body:
            suggestions.append("建议添加风险提示语")
        
        # 确定检查结果
        if issues:
            result = {
                "status": "BLOCK",
                "risk_level": "HIGH",
                "issues": issues,
                "suggestions": suggestions
            }
            status_str = "BLOCKED"
        else:
            result = {
                "status": "PASS",
                "risk_level": "LOW",
                "issues": issues,
                "suggestions": suggestions
            }
            status_str = "SUCCESS"
        
        state["compliance_result"] = result
        
        # 更新数据库记录
        async with async_session_maker() as session:
            from sqlalchemy import select
            db_result = await session.execute(
                select(Content).where(Content.workflow_id == workflow_id)
            )
            content_record = db_result.scalar_one_or_none()
            
            if content_record:
                content_record.compliance_result = result
                if result["status"] == "BLOCK":
                    # 合规检查失败，标记为待审核但记录问题
                    content_record.status = "reviewing"
                await session.commit()
        
        # 记录日志
        duration_ms = int((time.time() - start_time) * 1000)
        async with async_session_maker() as session:
            log = WorkflowLog(
                id=str(uuid.uuid4()),
                workflow_id=workflow_id,
                agent_name="Compliance Agent",
                action="内容合规审查",
                status=status_str,
                output_data=result,
                duration_ms=duration_ms,
                created_at=datetime.now()
            )
            session.add(log)
            await session.commit()
        
        if result["status"] == "BLOCK":
            print(f"[{workflow_id}] Compliance Agent: ⚠️ 内容审查发现问题 - {issues}")
        else:
            print(f"[{workflow_id}] Compliance Agent: ✅ 内容审查通过")
        
        return state
    
    async def human_review_node(self, state: WorkflowState) -> WorkflowState:
        """人工审核节点 - 等待用户通过API提交审核决策"""
        from app.core.database import async_session_maker
        from app.models.v4_models import WorkflowLog
        from app.services.openclaw_notify import notify_content_review
        
        workflow_id = state['workflow_id']
        
        content = state.get("content", {})
        compliance_result = state.get("compliance_result", {})
        
        # 检查合规检查结果
        if compliance_result.get("status") == "BLOCK":
            print(f"[{workflow_id}] Human Review: ⚠️ 内容存在合规问题，等待用户处理...")
            issues = compliance_result.get("issues", [])
            suggestions = compliance_result.get("suggestions", [])
            
            print(f"""
⚠️ 内容合规检查发现问题

标题: {content.get('titles', [''])[0]}

问题列表:
{chr(10).join(['❌ ' + issue for issue in issues])}

建议:
{chr(10).join(['💡 ' + suggestion for suggestion in suggestions])}

用户可以选择:
1. 重新创作 - 让AI重新生成内容
2. 强制通过 - 如果确认内容没有问题
3. 查看详情 - 在界面查看完整内容
""")
            
            # 通知 OpenClaw 合规问题
            try:
                await notify_content_review(
                    content_id="",
                    title=content.get('titles', [''])[0] if content.get('titles') else "无标题",
                    preview=f"⚠️ 合规检查发现问题: {', '.join(issues)}",
                    workflow_id=workflow_id
                )
            except Exception as e:
                print(f"[{workflow_id}] OpenClaw 通知发送失败: {e}")
        else:
            print(f"[{workflow_id}] Human Review: 等待用户审核...")
            print(f"""
📋 新内容等待审核

标题: {content.get('titles', [''])[0]}
正文预览: {content.get('body', '')[:100]}...

请在 Web 界面审核后调用 /api/v1/contents/{{id}}/review 提交审核结果
""")
        
        # 记录等待审核
        async with async_session_maker() as session:
            log = WorkflowLog(
                id=str(uuid.uuid4()),
                workflow_id=workflow_id,
                agent_name="Human Review",
                action="等待用户审核",
                status="PENDING",
                output_data={
                    "title": content.get('titles', [''])[0],
                    "compliance_status": compliance_result.get("status", "PASS"),
                    "issues": compliance_result.get("issues", [])
                },
                created_at=datetime.now()
            )
            session.add(log)
            await session.commit()
        
        # 设置为 None 表示等待用户决策
        state["review_decision"] = None
        state["revision_notes"] = None
        
        print(f"[{workflow_id}] Human Review: 等待用户决策")
        return state
    
    async def publish_node(self, state: WorkflowState) -> WorkflowState:
        """Publisher Agent: 准备发布，进入待审核状态"""
        from app.core.database import async_session_maker
        from app.models.v4_models import WorkflowLog
        from app.models import Content
        from app.services.openclaw_notify import notify_content_review
        
        workflow_id = state['workflow_id']
        print(f"[{workflow_id}] Publisher Agent: 创作完成，进入待审核状态...")
        
        content_data = state.get("content", {})
        
        # 验证内容有效性
        titles = content_data.get("titles", [])
        body = content_data.get("body", "")
        if not titles or not body or len(body) < 10:
            print(f"[{workflow_id}] Publisher Agent: 内容不完整，无法进入审核")
            raise WorkflowException(f"内容生成不完整: titles={len(titles)}, body={len(body)} 字符")
        
        # 查找对应的数据库记录（通过 workflow_id 关联）
        content_record = None
        async with async_session_maker() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Content).where(Content.workflow_id == workflow_id)
            )
            content_record = result.scalar_one_or_none()
            
            if content_record:
                # 更新状态为待审核，等待用户确认后自动发布
                content_record.status = "reviewing"
                await session.commit()
                await session.refresh(content_record)
                print(f"[{workflow_id}] Publisher Agent: 内容已就绪，等待用户审核")
            else:
                print(f"[{workflow_id}] Publisher Agent: 未找到对应的内容记录")
        
        state["published"] = False  # 标记为未发布，等待用户审核后自动发布
        
        # 记录日志
        async with async_session_maker() as session:
            log = WorkflowLog(
                id=str(uuid.uuid4()),
                workflow_id=workflow_id,
                agent_name="Publisher Agent",
                action="创作完成，进入待审核",
                status="SUCCESS",
                output_data={
                    "status": "reviewing",
                    "message": "内容已创作完成，请用户在界面审核确认"
                },
                created_at=datetime.now()
            )
            session.add(log)
            await session.commit()
        
        print(f"[{workflow_id}] Publisher Agent: 内容已就绪，请用户审核 ✅")
        
        # 通知 OpenClaw (小珑宝)，让它来通知用户
        try:
            titles = content_data.get("titles", [])
            title = titles[0] if titles else "无标题"
            preview = content_data.get("body", "")[:300]
            content_id = content_record.id if content_record else ""
            
            await notify_content_review(
                content_id=content_id,
                title=title,
                preview=preview,
                workflow_id=workflow_id
            )
            print(f"[{workflow_id}] OpenClaw 通知已发送 (小珑宝会通知用户)")
        except Exception as e:
            print(f"[{workflow_id}] OpenClaw 通知发送失败: {e}")
        
        return state
        
        return state
    
    async def analytics_node(self, state: WorkflowState) -> WorkflowState:
        """Analytics Agent: 数据分析"""
        from app.core.database import async_session_maker
        from app.models.v4_models import WorkflowLog
        
        workflow_id = state['workflow_id']
        print(f"[{workflow_id}] Analytics Agent: 记录数据...")
        
        # 记录完成
        async with async_session_maker() as session:
            log = WorkflowLog(
                id=str(uuid.uuid4()),
                workflow_id=workflow_id,
                agent_name="Analytics Agent",
                action="工作流完成",
                status="COMPLETED",
                output_data={
                    "published": state.get("published", False),
                    "revision_round": state.get("revision_round", 0)
                },
                created_at=datetime.now()
            )
            session.add(log)
            await session.commit()
        
        print(f"[{workflow_id}] Analytics Agent: 工作流执行记录已保存")
        return state
    
    def get_workflow_graph(self) -> str:
        """获取工作流的 Mermaid 图
        
        Returns:
            Mermaid 格式的流程图代码
        """
        if not self.workflow:
            return ""
        
        try:
            # 使用 LangGraph 的 get_graph 方法
            graph = self.workflow.get_graph()
            
            # 绘制 Mermaid 图
            mermaid_code = graph.draw_mermaid()
            
            return mermaid_code
        except Exception as e:
            print(f"[Orchestrator] 生成 Mermaid 图失败: {e}")
            # 返回一个简化的手动构建的图
            return """graph TD
    A[Research Agent<br/>热点研究] --> B[Compliance Check<br/>热点合规检查]
    B -->|合规| C[Creator Agent<br/>内容创作]
    B -->|不合规| A
    C --> D[Compliance Review<br/>内容合规审核]
    D -->|合规| E[Human Review<br/>人工审核]
    D -->|不合规| C
    E -->|通过| F[Publisher Agent<br/>准备发布]
    E -->|拒绝| C
    E -->|通过并发布| G[Analytics Agent<br/>数据分析]
    F --> G
            """
    
    async def run(self, user_id: str = "default", workflow_id: str = None) -> WorkflowState:
        """启动 Workflow
        
        Args:
            user_id: 用户ID
            workflow_id: 可选，指定 workflow_id（用于重新创作时关联原内容）
        """
        if workflow_id is None:
            workflow_id = f"wf_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        initial_state: WorkflowState = {
            "workflow_id": workflow_id,
            "user_id": user_id,
            "hot_topics": [],
            "selected_topic": None,
            "content": None,
            "compliance_result": None,
            "review_decision": None,
            "revision_notes": None,
            "revision_round": 0,
            "published": False,
            "error": None,
            "recent_topics": []
        }
        
        print(f"\n{'='*60}")
        print(f"🚀 启动 Workflow: {workflow_id}")
        print(f"{'='*60}\n")
        
        result = await self.workflow.ainvoke(initial_state)
        
        print(f"\n{'='*60}")
        print(f"✅ Workflow 完成: {workflow_id}")
        print(f"{'='*60}\n")
        
        return result


# 单例实例
orchestrator = None

try:
    orchestrator = OrchestratorAgent()
except Exception as e:
    print(f"[Orchestrator] 初始化失败: {e}")
    orchestrator = None

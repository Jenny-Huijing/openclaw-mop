"""
热点追踪服务
实现热点抓取、分析、推送全流程
"""
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from difflib import SequenceMatcher

from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.models import HotTopic, HotTopicTrend, HotTopicAlert
from app.services.search import search_service
from app.services.trending_platform import trending_service


class HotSpotService:
    """热点追踪服务"""
    
    # 分类关键词配置
    CATEGORIES = {
        "finance": {
            "name": "财经",
            "keywords": ["降息", "加息", "股市", "基金", "理财", "银行", "保险", "投资", "经济", "财经"],
            "weight": 1.5
        },
        "tech": {
            "name": "科技", 
            "keywords": ["AI", "人工智能", "芯片", "科技", "互联网", "手机", "电动车", "新能源"],
            "weight": 1.3
        },
        "lifestyle": {
            "name": "生活",
            "keywords": ["生活", "美食", "旅游", "家居", "穿搭", "护肤", "健身", "养生"],
            "weight": 1.0
        },
        "social": {
            "name": "社会",
            "keywords": ["社会", "民生", "教育", "医疗", "就业", "房价", "养老", "政策"],
            "weight": 1.2
        },
        "entertainment": {
            "name": "娱乐",
            "keywords": ["明星", "综艺", "电影", "电视剧", "音乐", "娱乐", "八卦"],
            "weight": 0.8
        }
    }
    
    # 推送阈值
    ALERT_THRESHOLD = {
        "new": 60,        # 新热点推送阈值
        "heat_rise": 50,  # 热度增长触发推送（百分比）
        "repeat": 50,     # 重复推送需要的热度增长
    }
    
    # 3天内不重复推送
    NO_REPEAT_DAYS = 3
    
    async def fetch_and_update_hotspots(self):
        """
        抓取并更新热点
        主入口：定时任务调用
        """
        print(f"[HotSpot] 开始抓取热点: {datetime.now()}")
        
        try:
            # 1. 从多个源抓取热点
            raw_hotspots = await self._fetch_from_sources()
            print(f"[HotSpot] 抓取到 {len(raw_hotspots)} 个原始热点")
            
            # 2. 处理和保存热点
            for hotspot_data in raw_hotspots:
                await self._process_hotspot(hotspot_data)
            
            # 3. 检查并推送特别热的热点
            await self._check_and_send_alerts()
            
            # 4. 清理过期热点
            await self._clean_expired_hotspots()
            
            print(f"[HotSpot] 热点更新完成")
            
        except Exception as e:
            print(f"[HotSpot] 抓取热点失败: {e}")
            import traceback
            traceback.print_exc()
    
    async def _fetch_from_sources(self) -> List[Dict]:
        """从多个源抓取热点"""
        hotspots = []
        
        # 1. 抓取多平台热搜数据
        platform_data = {}
        try:
            platform_data = await trending_service.fetch_all_trending()
            print(f"[HotSpot] 抓取多平台热搜: 微博{len(platform_data.get('weibo', []))}条, "
                  f"百度{len(platform_data.get('baidu', []))}条, "
                  f"知乎{len(platform_data.get('zhihu', []))}条, "
                  f"头条{len(platform_data.get('toutiao', []))}条")
        except Exception as e:
            print(f"[HotSpot] 抓取多平台热搜失败: {e}")
        
        # 2. 使用搜索服务抓取热点
        try:
            # 财经热点
            finance_results = await search_service.get_hotspots(count=10)
            for item in finance_results:
                title = item.get("title", "")
                
                # 计算多平台微热度分
                micro_heat = trending_service.calculate_micro_heat_score(title, platform_data)
                
                # 综合热度分 = 搜索热度分 * 0.7 + 微热度分 * 0.3
                search_score = item.get("heat_score", 50)
                micro_score = micro_heat.get('micro_heat_score', 50)
                final_score = int(search_score * 0.7 + micro_score * 0.3)
                
                # 如果有平台匹配，记录平台详情
                platform_info = micro_heat.get('platform_details', {})
                matched_platforms = list(platform_info.keys())
                
                hotspots.append({
                    "title": title,
                    "summary": item.get("summary", ""),
                    "heat_score": final_score,
                    "search_score": search_score,
                    "micro_score": micro_score,
                    "matched_platforms": matched_platforms,
                    "platform_details": platform_info,
                    "source": "search",
                    "source_url": item.get("url", ""),
                    "keywords": item.get("keywords", []),
                })
                
                if matched_platforms:
                    print(f"[HotSpot] 标题 '{title[:30]}...' 匹配平台: {matched_platforms}, "
                          f"微热度: {micro_score}, 综合: {final_score}")
        except Exception as e:
            print(f"[HotSpot] 抓取财经热点失败: {e}")
        
        # 3. 将多平台热搜中未匹配的热门话题也加入
        try:
            added_titles = {h['title'] for h in hotspots}
            
            for platform, items in platform_data.items():
                for item in items[:20]:  # 每个平台取前20
                    title = item.get('title', '')
                    
                    # 检查是否已经添加
                    if title in added_titles:
                        continue
                    
                    # 检查标题是否与已有热点相似
                    is_similar = False
                    for existing in hotspots:
                        similarity = SequenceMatcher(None, title.lower(), existing['title'].lower()).ratio()
                        if similarity > 0.7:
                            is_similar = True
                            break
                    
                    if not is_similar and title:
                        hotspots.append({
                            "title": title,
                            "summary": f"{platform}热搜榜第{item.get('rank')}名",
                            "heat_score": item.get('score', 50),
                            "search_score": 0,
                            "micro_score": item.get('score', 50),
                            "matched_platforms": [platform],
                            "platform_details": {platform: {
                                'rank': item.get('rank'),
                                'score': item.get('score'),
                                'matched_title': title,
                                'similarity': 1.0
                            }},
                            "source": platform,
                            "source_url": item.get('url', ''),
                            "keywords": [],
                        })
                        added_titles.add(title)
                        
        except Exception as e:
            print(f"[HotSpot] 处理多平台热搜失败: {e}")
        
        return hotspots
    
    async def _process_hotspot(self, data: Dict):
        """处理单个热点数据"""
        async with async_session_maker() as session:
            # 1. 检查是否已存在相似热点
            existing = await self._find_similar_topic(session, data["title"])
            
            if existing:
                # 更新现有热点
                await self._update_existing_topic(session, existing, data)
            else:
                # 创建新热点
                await self._create_new_topic(session, data)
            
            await session.commit()
    
    async def _find_similar_topic(self, session: AsyncSession, title: str) -> Optional[HotTopic]:
        """查找相似标题的热点（3天内）"""
        three_days_ago = datetime.utcnow() - timedelta(days=self.NO_REPEAT_DAYS)
        
        result = await session.execute(
            select(HotTopic)
            .where(HotTopic.discovered_at >= three_days_ago)
            .where(HotTopic.status != "expired")
            .order_by(desc(HotTopic.discovered_at))
        )
        topics = result.scalars().all()
        
        for topic in topics:
            # 使用相似度算法
            similarity = SequenceMatcher(None, topic.title, title).ratio()
            if similarity > 0.8:  # 80% 相似度视为同一热点
                return topic
        
        return None
    
    async def _update_existing_topic(self, session: AsyncSession, topic: HotTopic, data: Dict):
        """更新现有热点"""
        old_heat = topic.heat_score
        new_heat = data.get("heat_score", 0)
        
        # 更新热度
        topic.heat_score = max(old_heat, new_heat)
        topic.updated_at = datetime.utcnow()
        
        # 计算趋势
        if new_heat > old_heat * 1.3:
            topic.trend = "rising"
        elif new_heat < old_heat * 0.7:
            topic.trend = "falling"
        else:
            topic.trend = "stable"
        
        # 记录趋势
        trend = HotTopicTrend(
            id=str(uuid.uuid4()),
            topic_id=topic.id,
            heat_score=new_heat,
            recorded_at=datetime.utcnow()
        )
        session.add(trend)
        
        print(f"[HotSpot] 更新热点: {topic.title}, 热度: {old_heat} -> {new_heat}")
    
    async def _create_new_topic(self, session: AsyncSession, data: Dict):
        """创建新热点"""
        # 分类识别
        category = self._classify_topic(data.get("title", "") + " " + data.get("summary", ""))
        
        topic = HotTopic(
            id=str(uuid.uuid4()),
            title=data["title"],
            summary=data.get("summary", ""),
            heat_score=data.get("heat_score", 50),
            trend="stable",
            category=category,
            source=data.get("source", "unknown"),
            source_url=data.get("source_url", ""),
            keywords=data.get("keywords", []),
            discovered_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=self.NO_REPEAT_DAYS),
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
        
        print(f"[HotSpot] 创建新热点: {topic.title}, 分类: {category}, 热度: {topic.heat_score}")
    
    def _classify_topic(self, text: str) -> str:
        """自动分类热点"""
        text = text.lower()
        scores = {}
        
        for key, config in self.CATEGORIES.items():
            score = 0
            for keyword in config["keywords"]:
                if keyword.lower() in text:
                    score += 1
            scores[key] = score * config["weight"]
        
        if not scores or max(scores.values()) == 0:
            return "other"
        
        best_category = max(scores, key=scores.get)
        return best_category
    
    async def _check_and_send_alerts(self):
        """检查并发送推送"""
        async with async_session_maker() as session:
            # 1. 新热点（未推送且热度>60）
            new_hotspots = await session.execute(
                select(HotTopic)
                .where(HotTopic.is_notified == False)
                .where(HotTopic.heat_score >= self.ALERT_THRESHOLD["new"])
                .where(HotTopic.status.in_(['active', 'DISCOVERED', 'SELECTED']))
            )
            
            for topic in new_hotspots.scalars():
                await self._send_alert(session, topic, "new")
            
            # 2. 热度暴涨的热点
            three_days_ago = datetime.utcnow() - timedelta(days=self.NO_REPEAT_DAYS)
            recent_alerts = await session.execute(
                select(HotTopicAlert.topic_id)
                .where(HotTopicAlert.sent_at >= three_days_ago)
                .where(HotTopicAlert.alert_type == "new")
            )
            notified_ids = {row[0] for row in recent_alerts.all()}
            
            for topic_id in notified_ids:
                # 获取最新趋势
                trend_result = await session.execute(
                    select(HotTopicTrend)
                    .where(HotTopicTrend.topic_id == topic_id)
                    .order_by(desc(HotTopicTrend.recorded_at))
                    .limit(2)
                )
                trends = trend_result.scalars().all()
                
                if len(trends) >= 2:
                    latest = trends[0]
                    previous = trends[1]
                    
                    # 热度增长 > 50%
                    if previous.heat_score > 0 and (latest.heat_score - previous.heat_score) / previous.heat_score > 0.5:
                        topic = await session.get(HotTopic, topic_id)
                        if topic and topic.heat_score >= self.ALERT_THRESHOLD["heat_rise"]:
                            await self._send_alert(session, topic, "heat_rise")
            
            await session.commit()
    
    async def _send_alert(self, session: AsyncSession, topic: HotTopic, alert_type: str):
        """发送推送"""
        # 检查是否已经推送过
        existing = await session.execute(
            select(HotTopicAlert)
            .where(HotTopicAlert.topic_id == topic.id)
            .where(HotTopicAlert.alert_type == alert_type)
            .where(HotTopicAlert.sent_at >= datetime.utcnow() - timedelta(days=1))
        )
        if existing.scalar_one_or_none():
            return  # 今天已经推送过
        
        # 创建推送记录
        alert = HotTopicAlert(
            id=str(uuid.uuid4()),
            topic_id=topic.id,
            alert_type=alert_type,
            heat_score_at_send=topic.heat_score,
            sent_at=datetime.utcnow()
        )
        session.add(alert)
        
        # 标记热点已推送
        topic.is_notified = True
        
        # 发送到飞书
        await self._send_to_feishu(topic, alert_type)
        
        print(f"[HotSpot] 推送热点: {topic.title}, 类型: {alert_type}")
    
    async def _send_to_feishu(self, topic: HotTopic, alert_type: str):
        """发送到飞书"""
        try:
            from app.services.feishu import feishu_service
            
            # 生成创作角度
            angle = await self._generate_angle(topic)
            
            # 推送内容
            trend_emoji = {"rising": "🔥", "stable": "📊", "falling": "📉"}.get(topic.trend, "📊")
            type_text = {"new": "🆕 新热点", "heat_rise": "📈 热度暴涨", "daily_digest": "📰 每日精选"}.get(alert_type, "🔔 热点提醒")
            
            content = f"""{type_text} - {self.CATEGORIES.get(topic.category, {}).get('name', '其他')}

{trend_emoji} 【{topic.title}】
热度: {topic.heat_score}分 ({topic.trend})

💡 创作角度:
{angle}

📊 相关数据:
- 搜索热度: {topic.search_index}
- 讨论量: {topic.discuss_count}
- 阅读量: {topic.read_count}

🔗 来源: {topic.source_url or '未知'}

⏰ 推送时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
            
            # 这里需要实现飞书推送
            # await feishu_service.send_message(content)
            print(f"[HotSpot] 飞书推送内容:\n{content}")
            
        except Exception as e:
            print(f"[HotSpot] 飞书推送失败: {e}")
    
    async def _generate_angle(self, topic: HotTopic) -> str:
        """生成创作角度"""
        # 根据分类生成不同的角度
        angles = {
            "finance": [
                "从理财角度分析这对普通人的影响",
                "分享3个应对策略，帮你守住钱袋子",
                "解读政策背后的投资机会"
            ],
            "tech": [
                "这项技术如何改变我们的生活",
                "普通人如何抓住这次技术红利",
                "深度解析：这背后的商业逻辑"
            ],
            "lifestyle": [
                "亲测分享：我的真实体验",
                "避坑指南：这些细节要注意",
                "教你3招，轻松上手"
            ],
            "social": [
                "从民生角度解读这个热点",
                "这可能是你关心的话题",
                "政策解读：对我们有什么影响"
            ]
        }
        
        import random
        category_angles = angles.get(topic.category, ["这个热点值得关注"])
        return random.choice(category_angles)
    
    async def _clean_expired_hotspots(self):
        """清理过期热点"""
        async with async_session_maker() as session:
            expired = await session.execute(
                select(HotTopic)
                .where(HotTopic.expires_at <= datetime.utcnow())
                .where(HotTopic.status.in_(['active', 'DISCOVERED', 'SELECTED']))
            )
            
            for topic in expired.scalars():
                topic.status = "expired"
                print(f"[HotSpot] 热点过期: {topic.title}")
            
            await session.commit()
    
    async def get_hotspots(self, limit: int = 20, category: Optional[str] = None) -> List[Dict]:
        """获取热点列表"""
        async with async_session_maker() as session:
            query = select(HotTopic).where(HotTopic.status.in_(['active', 'DISCOVERED', 'SELECTED']))
            
            if category:
                query = query.where(HotTopic.category == category)
            
            query = query.order_by(desc(HotTopic.heat_score)).limit(limit)
            
            result = await session.execute(query)
            topics = result.scalars().all()
            
            return [topic.to_dict() for topic in topics]
    
    async def get_trend(self, topic_id: str) -> List[Dict]:
        """获取热点趋势"""
        async with async_session_maker() as session:
            result = await session.execute(
                select(HotTopicTrend)
                .where(HotTopicTrend.topic_id == topic_id)
                .order_by(HotTopicTrend.recorded_at)
                .limit(24)  # 最近24条记录
            )
            trends = result.scalars().all()
            return [trend.to_dict() for trend in trends]


# 单例
hotspot_service = HotSpotService()

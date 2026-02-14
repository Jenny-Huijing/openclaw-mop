"""
热点搜索服务 - 实时搜索当前财经热点
支持多个搜索源：百度热搜、微博热搜、知乎热榜等
"""

import os
import json
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
import aiohttp
from bs4 import BeautifulSoup

# API Keys (从环境变量或配置文件读取)
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY", "")

# 尝试从配置文件读取
try:
    from app.core.config import settings
    if settings.BRAVE_API_KEY:
        BRAVE_API_KEY = settings.BRAVE_API_KEY
except ImportError:
    pass


class HotspotSearchService:
    """热点搜索服务"""
    
    def __init__(self):
        self.brave_api_key = BRAVE_API_KEY
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建 HTTP Session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session
    
    async def search_brave(self, query: str, count: int = 10) -> List[Dict]:
        """
        使用 Brave Search API 搜索热点
        这是主要搜索方法，质量较高
        """
        if not self.brave_api_key:
            print("[Search] BRAVE_API_KEY not set, skipping Brave search")
            return []
        
        url = "https://api.search.brave.com/res/v1/news/search"
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.brave_api_key
        }
        params = {
            "q": query,
            "count": min(count, 20)
            # 移除不支持的参数，使用默认搜索
        }
        
        try:
            session = await self._get_session()
            async with session.get(url, headers=headers, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = []
                    for idx, item in enumerate(data.get("results", [])):
                        # 计算智能热度分
                        score = self._calculate_heat_score(item, idx)
                        results.append({
                            "title": item.get("title", ""),
                            "summary": item.get("description", ""),
                            "url": item.get("url", ""),
                            "source": item.get("source", {}).get("name", "未知来源"),
                            "published_at": item.get("published_at", ""),
                            "score": score
                        })
                    print(f"Brave search returned {len(results)} results")
                    return results
                elif resp.status == 422:
                    error_text = await resp.text()
                    print(f"Brave API error 422: {error_text}")
                    print(f"Request params: {params}")
                    return []
                else:
                    print(f"Brave API error: {resp.status}")
                    return []
        except Exception as e:
            print(f"Brave search failed: {e}")
            return []
    
    def _calculate_heat_score(self, item: Dict, rank: int) -> int:
        """
        计算智能热度分
        
        算法考虑因素：
        1. 搜索结果排名（越靠前分数越高）
        2. 发布时间（越新分数越高）
        3. 来源权威性（权威媒体加分）
        4. 标题关键词匹配度
        
        Returns: 0-100 的热度分
        """
        from datetime import datetime, timezone
        
        # 基础分：60-90 之间，根据排名递减
        base_score = max(60, 90 - rank * 3)
        
        # 1. 时效性加分（0-15分）
        time_bonus = 0
        published_at = item.get("published_at", "")
        if published_at:
            try:
                # 解析时间
                if isinstance(published_at, str):
                    # 尝试多种时间格式
                    try:
                        pub_time = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    except:
                        try:
                            pub_time = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%S")
                            pub_time = pub_time.replace(tzinfo=timezone.utc)
                        except:
                            pub_time = None
                else:
                    pub_time = None
                
                if pub_time:
                    now = datetime.now(timezone.utc)
                    hours_ago = (now - pub_time).total_seconds() / 3600
                    
                    if hours_ago < 1:
                        time_bonus = 15  # 1小时内最新
                    elif hours_ago < 6:
                        time_bonus = 12  # 6小时内
                    elif hours_ago < 24:
                        time_bonus = 8   # 24小时内
                    elif hours_ago < 48:
                        time_bonus = 5   # 48小时内
                    else:
                        time_bonus = 2   # 更旧的
            except Exception as e:
                print(f"[Search] 时间解析失败: {e}")
        
        # 2. 来源权威性加分（0-10分）
        source_bonus = 0
        source = item.get("source", {}).get("name", "").lower()
        authoritative_sources = {
            "新浪": 8, "sina": 8,
            "网易": 7, "163": 7,
            "搜狐": 7, "sohu": 7,
            "腾讯": 8, "qq": 8,
            "凤凰": 7, "ifeng": 7,
            "财新": 10, "caixin": 10,
            "华尔街": 9, "wsj": 9,
            "路透": 9, "reuters": 9,
            "彭博": 9, "bloomberg": 9,
            "央视": 10, "cctv": 10,
            "新华社": 10, "xinhua": 10,
            "人民日报": 10, "people": 10,
        }
        for key, bonus in authoritative_sources.items():
            if key in source:
                source_bonus = bonus
                break
        
        if source_bonus == 0:
            source_bonus = 5  # 未知来源默认5分
        
        # 3. 标题质量加分（0-5分）
        title = item.get("title", "")
        title_bonus = 0
        
        # 标题长度适中（20-60字符）加分
        title_len = len(title)
        if 20 <= title_len <= 60:
            title_bonus += 3
        elif 10 <= title_len < 20 or 60 < title_len <= 80:
            title_bonus += 1
        
        # 包含数字加分（如"降息0.25%"）
        if any(c.isdigit() for c in title):
            title_bonus += 2
        
        # 计算最终分数
        final_score = base_score + time_bonus + source_bonus + title_bonus
        
        # 限制在 0-100 范围内
        return min(100, max(0, final_score))
    
    async def search_finance_news(self) -> List[Dict]:
        """
        搜索财经新闻热点
        组合多个搜索词获取全面的财经热点
        """
        search_queries = [
            "央行 降准 降息 最新消息",
            "银行 存款 利率 调整",
            "LPR 房贷 利率 变化",
            "A股 股市 大涨 大跌",
            "黄金 价格 突破 新高",
            "个人养老金 政策 新动向",
            "数字人民币 试点 进展",
            "基金 理财 收益 排行",
            "房地产 政策 调控",
            "信用卡 新规 银行"
        ]
        
        all_results = []
        
        # 使用 Brave Search
        if self.brave_api_key:
            for query in search_queries[:5]:  # 取前5个关键词搜索
                try:
                    results = await self.search_brave(query, count=5)
                    all_results.extend(results)
                    await asyncio.sleep(0.5)  # 避免请求过快
                except Exception as e:
                    print(f"Search failed for '{query}': {e}")
        
        # 去重（基于标题相似度）
        unique_results = self._deduplicate_results(all_results)
        
        # 评分排序
        unique_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        print(f"Total unique finance hotspots: {len(unique_results)}")
        return unique_results[:15]  # 返回前15个
    
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """
        根据标题相似度去重
        """
        seen_titles = set()
        unique = []
        
        for result in results:
            title = result.get("title", "")
            # 简化的去重：检查标题是否包含已见标题的关键词
            is_duplicate = False
            for seen in seen_titles:
                # 如果标题相似度超过70%认为是重复
                if self._title_similarity(title, seen) > 0.7:
                    is_duplicate = True
                    break
            
            if not is_duplicate and title:
                seen_titles.add(title)
                unique.append(result)
        
        return unique
    
    def _title_similarity(self, title1: str, title2: str) -> float:
        """
        计算两个标题的相似度（简单版本）
        """
        # 提取关键词（去除常见词）
        stop_words = set(["的", "了", "是", "在", "和", "与", "或", "央行", "银行", "中国"])
        
        words1 = set([w for w in title1.lower() if w not in stop_words])
        words2 = set([w for w in title2.lower() if w not in stop_words])
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    def categorize_topic(self, title: str, summary: str = "") -> str:
        """
        对热点进行分类
        """
        text = (title + summary).lower()
        
        categories = {
            "货币政策": ["降准", "降息", "mlf", "lpr", "央行", "流动性"],
            "利率": ["利率", "房贷", "存款", "lpr"],
            "股市": ["a股", "股市", "大盘", "涨停", "跌停", "股票"],
            "贵金属": ["黄金", "白银", "金价", "贵金属"],
            "基金": ["基金", "定投", "公募", "私募", "基金经理"],
            "银行理财": ["理财", "净值", "收益率"],
            "房产": ["房地产", "房价", "楼市", "购房", "房贷"],
            "数字货币": ["数字人民币", "数字货币", "区块链"],
            "养老": ["养老金", "养老", "社保", "退休"],
            "信用卡": ["信用卡", "积分", "刷卡", "额度"],
        }
        
        for category, keywords in categories.items():
            if any(kw in text for kw in keywords):
                return category
        
        return "其他"
    
    async def get_hotspots(self, count: int = 10) -> List[Dict]:
        """
        获取热点列表（主入口）
        
        流程：
        1. 实时搜索财经新闻
        2. 分类整理
        3. 评分排序
        4. 返回结构化数据
        """
        print("Starting hotspot search...")
        
        # 搜索财经新闻
        news_results = await self.search_finance_news()
        
        # 构建热点列表
        hotspots = []
        for item in news_results[:count]:
            hotspot = {
                "id": f"hs_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(hotspots)}",
                "title": item["title"],
                "summary": item["summary"][:200] + "..." if len(item["summary"]) > 200 else item["summary"],
                "category": self.categorize_topic(item["title"], item["summary"]),
                "heat_score": item.get("score", 70),
                "professional_score": item.get("score", 70),
                "safety_score": 90,  # 财经新闻相对安全
                "innovation_score": 70,
                "total_score": item.get("score", 70),
                "source": item.get("source", "网络搜索"),
                "source_url": item.get("url", ""),
                "discovered_at": datetime.now().isoformat()
            }
            hotspots.append(hotspot)
        
        # 按总分排序
        hotspots.sort(key=lambda x: x["total_score"], reverse=True)
        
        print(f"Found {len(hotspots)} hotspots")
        return hotspots
    
    async def close(self):
        """关闭 Session"""
        if self.session and not self.session.closed:
            await self.session.close()


# 单例实例
search_service = HotspotSearchService()


# 便捷函数
async def search_hotspots(count: int = 10) -> List[Dict]:
    """搜索热点的便捷函数"""
    service = HotspotSearchService()
    try:
        return await service.get_hotspots(count)
    finally:
        await service.close()


if __name__ == "__main__":
    # 测试
    async def test():
        hotspots = await search_hotspots(5)
        print(json.dumps(hotspots, ensure_ascii=False, indent=2))
    
    asyncio.run(test())

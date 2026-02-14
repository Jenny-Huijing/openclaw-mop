"""
多平台热搜抓取服务
抓取微博、百度、知乎等平台的热搜榜
"""
import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import json
import asyncio

class TrendingPlatformService:
    """多平台热搜服务"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                }
            )
        return self.session
    
    async def fetch_weibo_hot(self) -> List[Dict]:
        """
        抓取微博热搜榜
        API: https://weibo.com/ajax/side/hotSearch
        """
        try:
            session = await self._get_session()
            url = "https://weibo.com/ajax/side/hotSearch"
            
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    realtime = data.get('data', {}).get('realtime', [])
                    
                    results = []
                    for item in realtime[:50]:  # 取前50
                        rank = item.get('rank', 0)
                        raw_hot = item.get('raw_hot', 0)
                        
                        # 微博热度归一化到0-100
                        # raw_hot 通常在 10万-500万之间
                        weibo_score = min(100, max(50, raw_hot / 50000))
                        
                        results.append({
                            'title': item.get('word', ''),
                            'rank': rank,
                            'hot_value': raw_hot,
                            'score': int(weibo_score),
                            'category': item.get('category', ''),
                            'source': 'weibo',
                            'url': f"https://s.weibo.com/weibo?q={item.get('word', '')}"
                        })
                    
                    print(f"[Trending] 微博热搜抓取成功: {len(results)}条")
                    return results
                else:
                    print(f"[Trending] 微博热搜抓取失败: {resp.status}")
                    return []
        except Exception as e:
            print(f"[Trending] 微博热搜异常: {e}")
            return []
    
    async def fetch_baidu_hot(self) -> List[Dict]:
        """
        抓取百度热搜榜
        API: https://top.baidu.com/board?tab=realtime
        """
        try:
            session = await self._get_session()
            url = "https://top.baidu.com/api/board?platform=wise&tab=realtime"
            
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    cards = data.get('data', {}).get('cards', [])
                    
                    results = []
                    for card in cards:
                        content = card.get('content', [])
                        for item in content[:50]:
                            rank = item.get('rank', 0)
                            raw_hot = item.get('hotScore', 0)
                            
                            # 百度热度归一化
                            # hotScore 通常在 100万-500万之间
                            baidu_score = min(100, max(50, raw_hot / 50000))
                            
                            results.append({
                                'title': item.get('word', ''),
                                'rank': rank,
                                'hot_value': raw_hot,
                                'score': int(baidu_score),
                                'category': item.get('category', ''),
                                'source': 'baidu',
                                'url': item.get('url', '')
                            })
                    
                    print(f"[Trending] 百度热搜抓取成功: {len(results)}条")
                    return results
                else:
                    print(f"[Trending] 百度热搜抓取失败: {resp.status}")
                    return []
        except Exception as e:
            print(f"[Trending] 百度热搜异常: {e}")
            return []
    
    async def fetch_zhihu_hot(self) -> List[Dict]:
        """
        抓取知乎热榜
        API: https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total
        """
        try:
            session = await self._get_session()
            url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50"
            
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    items = data.get('data', [])
                    
                    results = []
                    for item in items:
                        detail = item.get('target', {})
                        rank = len(results) + 1
                        
                        # 知乎没有直接热度值，用回答数和关注数估算
                        answer_count = detail.get('answer_count', 0)
                        follower_count = detail.get('follower_count', 0)
                        
                        # 估算热度分
                        zhihu_score = min(100, max(50, (answer_count + follower_count) / 1000))
                        
                        results.append({
                            'title': detail.get('title', ''),
                            'rank': rank,
                            'hot_value': answer_count + follower_count,
                            'score': int(zhihu_score),
                            'category': '',
                            'source': 'zhihu',
                            'url': f"https://www.zhihu.com/question/{detail.get('id', '')}"
                        })
                    
                    print(f"[Trending] 知乎热榜抓取成功: {len(results)}条")
                    return results
                else:
                    print(f"[Trending] 知乎热榜抓取失败: {resp.status}")
                    return []
        except Exception as e:
            print(f"[Trending] 知乎热榜异常: {e}")
            return []
    
    async def fetch_toutiao_hot(self) -> List[Dict]:
        """
        抓取今日头条热榜
        """
        try:
            session = await self._get_session()
            url = "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc"
            
            async with session.get(url) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    results = []
                    # 解析热榜列表
                    items = soup.select('.board-item') or soup.select('[data-e2e-name="hot-board-item"]')
                    
                    for idx, item in enumerate(items[:50], 1):
                        title_elem = item.select_one('.title') or item.select_one('a')
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            
                            # 今日头条热度值
                            hot_elem = item.select_one('.hot-value') or item.select_one('.heat')
                            hot_value = int(hot_elem.get_text(strip=True).replace('万', '0000')) if hot_elem else 0
                            
                            # 归一化
                            toutiao_score = min(100, max(50, hot_value / 10000))
                            
                            results.append({
                                'title': title,
                                'rank': idx,
                                'hot_value': hot_value,
                                'score': int(toutiao_score),
                                'category': '',
                                'source': 'toutiao',
                                'url': title_elem.get('href', '')
                            })
                    
                    print(f"[Trending] 今日头条热榜抓取成功: {len(results)}条")
                    return results
                else:
                    print(f"[Trending] 今日头条抓取失败: {resp.status}")
                    return []
        except Exception as e:
            print(f"[Trending] 今日头条异常: {e}")
            return []
    
    async def fetch_all_trending(self) -> Dict[str, List[Dict]]:
        """
        抓取所有平台的热搜
        """
        results = await asyncio.gather(
            self.fetch_weibo_hot(),
            self.fetch_baidu_hot(),
            self.fetch_zhihu_hot(),
            self.fetch_toutiao_hot(),
            return_exceptions=True
        )
        
        return {
            'weibo': results[0] if not isinstance(results[0], Exception) else [],
            'baidu': results[1] if not isinstance(results[1], Exception) else [],
            'zhihu': results[2] if not isinstance(results[2], Exception) else [],
            'toutiao': results[3] if not isinstance(results[3], Exception) else [],
        }
    
    def calculate_micro_heat_score(self, title: str, platform_data: Dict[str, List[Dict]]) -> Dict:
        """
        计算微热度分
        
        算法：
        1. 在各个平台热搜中查找匹配
        2. 匹配到的平台数量和排名加权
        3. 返回微热度分和平台分布
        """
        import difflib
        
        platform_scores = {}
        total_score = 0
        matched_count = 0
        
        for platform, items in platform_data.items():
            best_match = None
            best_score = 0
            
            for item in items:
                # 计算标题相似度
                similarity = difflib.SequenceMatcher(None, title.lower(), item['title'].lower()).ratio()
                
                if similarity > 0.6 and similarity > best_score:  # 60%相似度阈值
                    best_match = item
                    best_score = similarity
            
            if best_match:
                # 平台权重：排名越靠前权重越高
                rank_weight = max(0.5, 1 - (best_match['rank'] - 1) * 0.02)  # 排名1权重1，排名50权重0.5
                platform_score = best_match['score'] * rank_weight
                
                platform_scores[platform] = {
                    'rank': best_match['rank'],
                    'score': int(best_match['score']),
                    'matched_title': best_match['title'],
                    'similarity': round(best_score, 2)
                }
                
                total_score += platform_score
                matched_count += 1
        
        # 多平台匹配加分
        cross_platform_bonus = min(20, (matched_count - 1) * 10) if matched_count > 1 else 0
        
        final_score = min(100, int(total_score / max(1, matched_count) + cross_platform_bonus))
        
        return {
            'micro_heat_score': final_score,
            'matched_platforms': matched_count,
            'platform_details': platform_scores
        }
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()


# 单例实例
trending_service = TrendingPlatformService()

# 便捷函数
async def get_multi_platform_trending() -> Dict[str, List[Dict]]:
    """获取多平台热搜"""
    service = TrendingPlatformService()
    try:
        return await service.fetch_all_trending()
    finally:
        await service.close()

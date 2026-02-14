"""
小红书账号数据爬虫
用于获取真实的账号运营数据

支持两种方式（优先级）：
1. MCP 服务（xiaohongshu-mcp）- 推荐，更稳定
2. 传统 Cookie 爬虫 - 备选
"""

import os
import re
import json
import asyncio
from typing import Optional, Dict, List
from dataclasses import dataclass
import aiohttp
from bs4 import BeautifulSoup

from app.core.config import settings

# 延迟导入 MCP 客户端，避免循环依赖
_mcp_client = None

def _get_mcp_client():
    """延迟获取 MCP 客户端"""
    global _mcp_client
    if _mcp_client is None and settings.MCP_ENABLED:
        from app.services.xhs_mcp import get_mcp_client
        _mcp_client = get_mcp_client()
    return _mcp_client


@dataclass
class XHSNote:
    """小红书笔记数据"""
    note_id: str
    title: str
    content: str
    likes: int
    comments: int
    collects: int
    views: int
    created_time: str
    tags: List[str]


@dataclass
class XHSAccount:
    """小红书账号数据"""
    user_id: str
    nickname: str
    avatar: str
    followers: int
    following: int
    total_notes: int
    total_likes: int
    bio: str


class XHSCrawler:
    """
    小红书数据爬虫
    
    使用方法:
    1. 登录小红书网页版 https://www.xiaohongshu.com
    2. 在浏览器开发者工具中获取 Cookie
    3. 设置环境变量 XHS_COOKIE
    """
    
    BASE_URL = "https://www.xiaohongshu.com"
    API_URL = "https://edith.xiaohongshu.com"
    
    def __init__(self):
        # 优先从文件读取 Cookie
        cookie_file = "/app/data/cookies.json"
        cookie_from_env = os.getenv("XHS_COOKIE", "")
        
        if os.path.exists(cookie_file):
            try:
                with open(cookie_file, 'r') as f:
                    cookies = json.load(f)
                    # 将 cookies 转换为请求头格式
                    cookie_str = '; '.join([f"{c['name']}={c['value']}" for c in cookies])
                    self.cookie = cookie_str
                    print("[XHS] 从文件加载 Cookie 成功")
            except Exception as e:
                print(f"[XHS] 从文件加载 Cookie 失败: {e}")
                self.cookie = cookie_from_env
        else:
            self.cookie = cookie_from_env
        
        self.user_agent = os.getenv(
            "XHS_USER_AGENT",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.xiaohongshu.com/",
            "Origin": "https://www.xiaohongshu.com",
            "Cookie": self.cookie,
        }
    
    def _check_cookie(self) -> bool:
        """检查Cookie是否配置"""
        if not self.cookie:
            print("[XHS] 警告: XHS_COOKIE 未配置，无法获取真实数据")
            return False
        return True
    
    async def get_account_info(self, user_id: Optional[str] = None) -> Optional[XHSAccount]:
        """
        获取账号基本信息
        
        Args:
            user_id: 用户ID，如果不传则获取当前登录用户
        """
        if not self._check_cookie():
            return None
        
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                # 获取个人主页数据
                if user_id:
                    url = f"{self.BASE_URL}/user/profile/{user_id}"
                else:
                    url = f"{self.BASE_URL}/user/me"
                
                async with session.get(url) as response:
                    if response.status != 200:
                        print(f"[XHS] 请求失败: {response.status}")
                        return None
                    
                    html = await response.text()
                    
                    # 解析页面数据
                    account = self._parse_account_page(html)
                    return account
                    
        except Exception as e:
            print(f"[XHS] 获取账号信息失败: {e}")
            return None
    
    def _parse_account_page(self, html: str) -> Optional[XHSAccount]:
        """解析账号页面HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 查找包含用户数据的script标签
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'window.__INITIAL_STATE__' in script.string:
                    # 提取JSON数据
                    match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.+?});', script.string)
                    if match:
                        data = json.loads(match.group(1))
                        return self._extract_account_from_json(data)
            
            # 备选：从meta标签提取
            return self._parse_account_from_meta(soup)
            
        except Exception as e:
            print(f"[XHS] 解析页面失败: {e}")
            return None
    
    def _extract_account_from_json(self, data: dict) -> Optional[XHSAccount]:
        """从JSON数据中提取账号信息"""
        try:
            user = data.get('user', {})
            if not user:
                user = data.get('userInfo', {})
            
            return XHSAccount(
                user_id=str(user.get('userId', '')),
                nickname=user.get('nickname', ''),
                avatar=user.get('avatar', ''),
                followers=user.get('followers', 0),
                following=user.get('following', 0),
                total_notes=user.get('notes', 0),
                total_likes=user.get('liked', 0),
                bio=user.get('desc', '')
            )
        except Exception as e:
            print(f"[XHS] 提取账号信息失败: {e}")
            return None
    
    def _parse_account_from_meta(self, soup: BeautifulSoup) -> Optional[XHSAccount]:
        """从meta标签解析账号信息（备选方案）"""
        try:
            # 昵称
            nickname_meta = soup.find('meta', property='og:title')
            nickname = nickname_meta['content'] if nickname_meta else ''
            
            # 头像
            avatar_meta = soup.find('meta', property='og:image')
            avatar = avatar_meta['content'] if avatar_meta else ''
            
            # 从页面文本中提取粉丝数
            text = soup.get_text()
            
            # 匹配粉丝数
            followers_match = re.search(r'粉丝[\s:：]*(\d+(?:\.\d+)?[万kK]?)', text)
            followers = self._parse_number(followers_match.group(1) if followers_match else '0')
            
            # 匹配关注数
            following_match = re.search(r'关注[\s:：]*(\d+(?:\.\d+)?[万kK]?)', text)
            following = self._parse_number(following_match.group(1) if following_match else '0')
            
            # 匹配笔记数
            notes_match = re.search(r'笔记[\s:：]*(\d+(?:\.\d+)?[万kK]?)', text)
            total_notes = self._parse_number(notes_match.group(1) if notes_match else '0')
            
            return XHSAccount(
                user_id='',
                nickname=nickname,
                avatar=avatar,
                followers=followers,
                following=following,
                total_notes=total_notes,
                total_likes=0,
                bio=''
            )
            
        except Exception as e:
            print(f"[XHS] Meta解析失败: {e}")
            return None
    
    def _parse_number(self, text: str) -> int:
        """解析数字（支持万/K单位）"""
        if not text:
            return 0
        
        text = text.strip().lower()
        
        # 处理万
        if '万' in text or 'w' in text:
            num = float(re.sub(r'[^\d.]', '', text))
            return int(num * 10000)
        
        # 处理K
        if 'k' in text:
            num = float(re.sub(r'[^\d.]', '', text))
            return int(num * 1000)
        
        # 纯数字
        try:
            return int(re.sub(r'[^\d]', '', text))
        except:
            return 0
    
    async def get_notes(self, user_id: Optional[str] = None, limit: int = 20) -> List[XHSNote]:
        """
        获取用户笔记列表
        
        Args:
            user_id: 用户ID
            limit: 获取数量
        """
        if not self._check_cookie():
            return []
        
        notes = []
        
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                # 构建API请求
                params = {
                    "num": limit,
                    "cursor": ""
                }
                
                if user_id:
                    url = f"{self.API_URL}/api/sns/web/v1/user_posted"
                    params["user_id"] = user_id
                else:
                    url = f"{self.API_URL}/api/sns/web/v1/user_posted"
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        notes = self._parse_notes_response(data)
                    else:
                        print(f"[XHS] 获取笔记失败: {response.status}")
                        
        except Exception as e:
            print(f"[XHS] 获取笔记列表失败: {e}")
        
        return notes
    
    def _parse_notes_response(self, data: dict) -> List[XHSNote]:
        """解析笔记API响应"""
        notes = []
        
        try:
            if data.get('code') != 0:
                print(f"[XHS] API错误: {data.get('msg')}")
                return notes
            
            note_list = data.get('data', {}).get('notes', [])
            
            for item in note_list:
                note = XHSNote(
                    note_id=item.get('note_id', ''),
                    title=item.get('title', ''),
                    content=item.get('desc', ''),
                    likes=item.get('likes', 0),
                    comments=item.get('comments', 0),
                    collects=item.get('collected', 0),
                    views=item.get('views', 0),
                    created_time=item.get('time', ''),
                    tags=item.get('tag_list', [])
                )
                notes.append(note)
                
        except Exception as e:
            print(f"[XHS] 解析笔记失败: {e}")
        
        return notes


# 单例实例
_xhs_crawler = None
_mcp_client = None

# 缓存
_cached_account_stats = None
_cache_time = 0
_CACHE_TTL = 300  # 缓存5分钟

def get_xhs_crawler() -> XHSCrawler:
    """获取小红书爬虫实例"""
    global _xhs_crawler
    if _xhs_crawler is None:
        _xhs_crawler = XHSCrawler()
    return _xhs_crawler


def _get_mcp_client():
    """延迟获取 MCP 客户端"""
    global _mcp_client
    if _mcp_client is None and settings.MCP_ENABLED:
        from app.services.xhs_mcp import get_mcp_client
        _mcp_client = get_mcp_client()
    return _mcp_client


async def fetch_account_stats() -> Optional[Dict]:
    """
    获取账号统计数据（供API调用）
    
    优先使用传统爬虫获取当前登录用户数据，失败则回退到 MCP
    
    Returns:
        {
            "followers": 粉丝数,
            "following": 关注数,
            "total_notes": 笔记总数,
            "total_likes": 总获赞数,
            "nickname": 昵称,
            "avatar": 头像URL,
            "source": "mcp" | "crawler"
        }
    """
    global _cached_account_stats, _cache_time
    
    # 检查缓存（调试用：暂时禁用缓存）
    import time
    current_time = time.time()
    # if _cached_account_stats and (current_time - _cache_time) < _CACHE_TTL:
    #     print("[XHS] 使用缓存的账号数据")
    #     return _cached_account_stats
    
    # 优先使用 MCP 服务
    if settings.MCP_ENABLED:
        try:
            mcp_client = _get_mcp_client()
            if mcp_client:
                from app.services.xhs_mcp import fetch_account_stats_via_mcp
                # 使用配置的 XHS_USER_ID 或从推荐流自动获取
                result = await fetch_account_stats_via_mcp(user_id=settings.XHS_USER_ID)
                # 检查数据有效性
                if result and result.get("nickname") and result.get("nickname") not in ["xiaohongshu-mcp", "", None]:
                    print(f"[XHS] 通过 MCP 获取账号数据成功: {result.get('nickname')}")
                    # 更新缓存
                    _cached_account_stats = result
                    _cache_time = current_time
                    return result
                else:
                    print(f"[XHS] MCP 返回无效数据: {result}")
        except Exception as e:
            print(f"[XHS] MCP 获取失败: {e}")
            import traceback
            traceback.print_exc()
    
    # 回退到传统爬虫获取当前登录用户数据
    crawler = get_xhs_crawler()
    account = await crawler.get_account_info()
    
    if account and account.nickname and account.nickname != "xiaohongshu-mcp":  # 确保有昵称才算成功
        result = {
            "followers": account.followers,
            "following": account.following,
            "total_notes": account.total_notes,
            "total_likes": account.total_likes,
            "nickname": account.nickname,
            "avatar": account.avatar,
            "bio": account.bio,
            "source": "crawler"
        }
        print(f"[XHS] 通过爬虫获取当前用户账号数据成功: {account.nickname}")
        # 更新缓存
        _cached_account_stats = result
        _cache_time = current_time
        return result
    
    return None


async def fetch_recent_notes(limit: int = 10) -> List[Dict]:
    """
    获取最近笔记数据（供API调用）
    
    优先使用 MCP 服务，失败则回退到传统爬虫
    
    Returns:
        [{
            "note_id": 笔记ID,
            "title": 标题,
            "likes": 点赞数,
            "comments": 评论数,
            "collects": 收藏数,
            "views": 浏览数,
            "source": "mcp" | "crawler"
        }]
    """
    # 优先尝试 MCP 服务
    if settings.MCP_ENABLED:
        try:
            mcp_client = _get_mcp_client()
            if mcp_client:
                from app.services.xhs_mcp import fetch_recent_notes_via_mcp
                result = await fetch_recent_notes_via_mcp(limit=limit)
                if result:
                    print(f"[XHS] 通过 MCP 获取 {len(result)} 条笔记成功")
                    return result
        except Exception as e:
            print(f"[XHS] MCP 获取笔记失败，回退到爬虫: {e}")
    
    # 回退到传统爬虫
    crawler = get_xhs_crawler()
    notes = await crawler.get_notes(limit=limit)
    
    return [
        {
            "note_id": n.note_id,
            "title": n.title,
            "likes": n.likes,
            "comments": n.comments,
            "collects": n.collects,
            "views": n.views,
            "created_time": n.created_time,
            "source": "crawler"
        }
        for n in notes
    ]


# 测试代码
if __name__ == "__main__":
    async def test():
        crawler = XHSCrawler()
        
        # 获取账号信息
        account = await crawler.get_account_info()
        if account:
            print(f"昵称: {account.nickname}")
            print(f"粉丝: {account.followers}")
            print(f"笔记: {account.total_notes}")
        
        # 获取笔记
        notes = await crawler.get_notes(limit=5)
        for note in notes:
            print(f"- {note.title}: {note.likes}赞 {note.comments}评论")
    
    asyncio.run(test())

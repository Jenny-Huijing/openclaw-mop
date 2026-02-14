"""
小红书 MCP 客户端

使用标准 MCP Streamable HTTP 协议与 xiaohongshu-mcp 服务通信
"""

import json
import asyncio
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
import aiohttp
from app.core.config import settings


@dataclass
class XHSNoteDetail:
    """小红书笔记详情"""
    note_id: str
    title: str
    content: str
    likes: int
    comments: int
    collects: int
    share_count: int
    user_id: str
    nickname: str
    tags: List[str]
    images: List[str]
    created_time: str


@dataclass
class XHSUserProfile:
    """小红书用户资料"""
    user_id: str
    nickname: str
    avatar: str
    followers: int
    following: int
    notes_count: int
    likes_count: int
    bio: str


class XHSMCPClient:
    """
    小红书 MCP 客户端
    
    通过标准 MCP Streamable HTTP 协议与 xiaohongshu-mcp 服务通信
    """
    
    def __init__(self, mcp_url: Optional[str] = None):
        self.mcp_url = mcp_url or settings.MCP_URL
        self.enabled = settings.MCP_ENABLED
        self.session: Optional[aiohttp.ClientSession] = None
        self._session_id: Optional[str] = None
        self._initialized = False
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取 HTTP 会话"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={"Content-Type": "application/json"}
            )
        return self.session
    
    async def _ensure_initialized(self) -> bool:
        """
        确保 MCP 会话已初始化
        
        Returns:
            bool: 初始化是否成功
        """
        if self._initialized and self._session_id:
            return True
        
        if not self.enabled:
            return False
        
        try:
            session = await self._get_session()
            
            # 1. Initialize
            init_payload = {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "xhs-platform", "version": "1.0.0"}
                }
            }
            
            async with session.post(
                self.mcp_url,
                json=init_payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if "result" in result:
                        # 获取 Session ID
                        self._session_id = response.headers.get('Mcp-Session-Id')
                        if not self._session_id:
                            print("[MCP] 警告: 未获取到 Session ID")
                            return False
                    else:
                        return False
                else:
                    return False
            
            # 2. Send initialized notification
            init_notify = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {}
            }
            
            headers = {
                "Content-Type": "application/json",
                "Mcp-Session-Id": self._session_id
            }
            
            async with session.post(
                self.mcp_url,
                json=init_notify,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 202:
                    self._initialized = True
                    return True
            
            return False
            
        except Exception as e:
            print(f"[MCP] 初始化失败: {e}")
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        """获取带 Session ID 的请求头"""
        headers = {"Content-Type": "application/json"}
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id
        return headers
    
    async def _call_tool(self, tool_name: str, arguments: Dict = None, timeout: int = 30) -> Dict:
        """
        调用 MCP 工具
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            timeout: 超时时间（秒），默认30秒
        
        Returns:
            工具调用结果
        """
        if not await self._ensure_initialized():
            return {"error": "MCP 会话未初始化"}
        
        session = await self._get_session()
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {}
            }
        }
        
        try:
            async with session.post(
                self.mcp_url,
                json=payload,
                headers=self._get_headers(),
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                text = await response.text()
                if not text:
                    return {"error": "空响应"}
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return {"error": f"无效JSON: {text[:100]}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def check_login_status(self) -> Dict:
        """检查登录状态"""
        result = await self._call_tool("check_login_status", {})
        
        if "error" in result:
            return {"logged_in": False, "error": result["error"]}
        
        try:
            content = result.get("result", {}).get("content", [])
            if content:
                text = content[0].get("text", "")
                # 解析文本响应
                logged_in = "✅ 已登录" in text
                username = None
                if "用户名:" in text:
                    username = text.split("用户名:")[1].strip().split("\n")[0]
                return {"logged_in": logged_in, "username": username}
        except Exception as e:
            return {"logged_in": False, "error": str(e)}
        
        return {"logged_in": False}
    
    async def get_notes(self, limit: int = 20) -> List[Dict]:
        """
        获取笔记列表 (通过 list_feeds)
        
        Args:
            limit: 获取数量
        """
        result = await self._call_tool("list_feeds", {})
        
        if "error" in result:
            print(f"[MCP] 获取笔记列表失败: {result['error']}")
            return []
        
        try:
            content = result.get("result", {}).get("content", [])
            if content and len(content) > 0:
                text_data = content[0].get("text", "{}")
                data = json.loads(text_data)
                feeds = data.get("feeds", [])[:limit]
                return [
                    {
                        "note_id": f.get("id", ""),
                        "title": f.get("noteCard", {}).get("displayTitle", ""),
                        "content": "",
                        "likes": int(f.get("noteCard", {}).get("interactInfo", {}).get("likedCount", 0)),
                        "comments": 0,
                        "collects": 0,
                        "user_id": f.get("noteCard", {}).get("user", {}).get("userId", ""),
                        "nickname": f.get("noteCard", {}).get("user", {}).get("nickname", ""),
                        "images": [],
                        "created_time": ""
                    }
                    for f in feeds
                ]
        except Exception as e:
            print(f"[MCP] 解析笔记列表失败: {e}")
        return []
    
    async def search_notes(self, keyword: str, limit: int = 20) -> List[Dict]:
        """
        搜索笔记
        
        Args:
            keyword: 搜索关键词
            limit: 返回数量
        """
        result = await self._call_tool("search_feeds", {"keyword": keyword})
        
        if "error" in result:
            print(f"[MCP] 搜索笔记失败: {result['error']}")
            return []
        
        try:
            content = result.get("result", {}).get("content", [])
            if content and len(content) > 0:
                text_data = content[0].get("text", "{}")
                data = json.loads(text_data)
                feeds = data.get("feeds", [])[:limit]
                return [
                    {
                        "note_id": f.get("id", ""),
                        "title": f.get("title", ""),
                        "content": f.get("desc", ""),
                        "likes": f.get("likes", 0),
                        "comments": f.get("comments", 0),
                        "user_id": f.get("user", {}).get("id", ""),
                        "nickname": f.get("user", {}).get("nickname", ""),
                    }
                    for f in feeds
                ]
        except Exception as e:
            print(f"[MCP] 解析搜索结果失败: {e}")
        return []
    
    async def publish_note(self, title: str, content: str, images: List[str],
                          tags: Optional[List[str]] = None) -> Dict:
        """
        发布笔记
        
        Args:
            title: 标题
            content: 正文内容
            images: 图片路径列表（支持本地绝对路径或HTTP链接）
            tags: 标签列表
        
        Returns:
            发布结果
        """
        # 发布需要更长时间（上传图片+发布），设置120秒超时
        result = await self._call_tool("publish_content", {
            "title": title,
            "content": content,
            "images": images,
            "tags": tags or []
        }, timeout=120)
        
        if "error" in result:
            return {"success": False, "error": result["error"]}
        
        # 解析 MCP 返回的内容，检查是否真的发布成功
        try:
            print(f"[MCP] 发布返回结果: {result}")
            content_list = result.get("result", {}).get("content", [])
            if content_list and len(content_list) > 0:
                text = content_list[0].get("text", "")
                print(f"[MCP] 发布返回文本: {text}")
                # 检查是否包含成功关键词
                if "成功" in text or "发布完成" in text or "✅" in text or "note_id" in text:
                    return {"success": True, "data": result.get("result", {}), "message": text}
                elif "失败" in text or "错误" in text or "❌" in text:
                    # 包含明确的错误信息
                    return {"success": False, "error": text}
                else:
                    # 无法确定是否成功，记录警告
                    print(f"[MCP] 警告: 无法确定发布是否成功，返回文本: {text}")
                    return {"success": False, "error": text or "发布状态未知，请手动检查小红书"}
        except Exception as e:
            print(f"[MCP] 解析发布结果失败: {e}")
            return {"success": False, "error": f"解析发布结果失败: {str(e)}"}
        
        return {"success": False, "error": "无法解析 MCP 返回结果"}
    
    async def close(self):
        """关闭会话"""
        if self.session and not self.session.closed:
            await self.session.close()
        self._initialized = False
        self._session_id = None


# 单例实例
_mcp_client: Optional[XHSMCPClient] = None

def get_mcp_client() -> XHSMCPClient:
    """获取 MCP 客户端实例"""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = XHSMCPClient()
    return _mcp_client


async def fetch_account_stats_via_mcp(user_id: Optional[str] = None) -> Optional[Dict]:
    """通过 MCP 获取账号统计数据
    
    Args:
        user_id: 可选，指定用户ID。如果不传，则从推荐流中获取
    """
    client = get_mcp_client()
    
    # 检查登录状态
    login_status = await client.check_login_status()
    if not login_status.get("logged_in"):
        return None
    
    # 获取 xsec_token（从推荐流中）
    result = await client._call_tool("list_feeds", {})
    xsec_token = None
    try:
        content = result.get("result", {}).get("content", [])
        if content:
            data = json.loads(content[0].get("text", "{}"))
            feeds = data.get("feeds", [])
            if feeds:
                xsec_token = feeds[0].get("xsecToken")
    except Exception as e:
        print(f"[MCP] 获取 xsec_token 失败: {e}")
    
    # 如果没有指定 user_id，尝试从推荐流获取
    if not user_id:
        try:
            content = result.get("result", {}).get("content", [])
            if content:
                data = json.loads(content[0].get("text", "{}"))
                feeds = data.get("feeds", [])
                if feeds:
                    note_card = feeds[0].get("noteCard", {})
                    user = note_card.get("user", {})
                    user_id = user.get("userId")
        except Exception as e:
            print(f"[MCP] 从推荐流获取 user_id 失败: {e}")
    
    # 调用 user_profile 获取完整信息
    if user_id and xsec_token:
        try:
            print(f"[MCP] Calling user_profile with user_id={user_id}")
            profile_result = await client._call_tool("user_profile", {
                "user_id": user_id,
                "xsec_token": xsec_token
            })
            print(f"[MCP] user_profile result: {profile_result}")
            
            if "result" in profile_result:
                profile_content = profile_result["result"].get("content", [])
                if profile_content:
                    profile_data = json.loads(profile_content[0].get("text", "{}"))
                    user_basic = profile_data.get("userBasicInfo", {})
                    interactions = profile_data.get("interactions", [])
                    feeds_list = profile_data.get("feeds", [])
                    
                    # 解析互动数据
                    followers = 0
                    following = 0
                    total_likes = 0
                    
                    for interaction in interactions:
                        if interaction.get("type") == "fans":
                            followers = int(interaction.get("count", 0))
                        elif interaction.get("type") == "follows":
                            following = int(interaction.get("count", 0))
                        elif interaction.get("type") == "interaction":
                            total_likes = int(interaction.get("count", 0))
                    
                    return {
                        "nickname": user_basic.get("nickname", login_status.get("username", "")),
                        "avatar": user_basic.get("images", ""),
                        "followers": followers,
                        "following": following,
                        "total_notes": len(feeds_list),
                        "total_likes": total_likes,
                        "bio": user_basic.get("desc", ""),
                        "location": user_basic.get("ipLocation", ""),
                        "logged_in": True,
                        "source": "mcp"
                    }
        except Exception as e:
            print(f"[MCP] 获取用户资料失败: {e}")
    
    # 降级返回基本数据
    return {
        "nickname": login_status.get("username", ""),
        "avatar": "",
        "followers": 0,
        "following": 0,
        "total_notes": 0,
        "total_likes": 0,
        "logged_in": True,
        "source": "mcp"
    }


async def fetch_recent_notes_via_mcp(limit: int = 10) -> List[Dict]:
    """通过 MCP 获取最近笔记数据"""
    client = get_mcp_client()
    notes = await client.get_notes(limit=limit)
    
    return [
        {
            "note_id": n["note_id"],
            "title": n["title"],
            "content": n["content"][:200] + "..." if len(n["content"]) > 200 else n["content"],
            "likes": n["likes"],
            "comments": n["comments"],
            "collects": n["collects"],
            "nickname": n["nickname"],
            "source": "mcp"
        }
        for n in notes
    ]


# 健康检查
async def check_mcp_health() -> Dict:
    """检查 MCP 服务健康状态"""
    try:
        client = get_mcp_client()
        if await client._ensure_initialized():
            return {
                "healthy": True,
                "session_id": client._session_id[:20] + "..." if client._session_id else None,
                "url": settings.MCP_URL
            }
        return {"healthy": False, "error": "初始化失败"}
    except Exception as e:
        return {"healthy": False, "error": str(e)}


# 导出单例实例供其他模块使用
mcp_service = get_mcp_client()

"""
小红书账号数据API
使用 MCP 服务获取数据
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.xhs_crawler import fetch_account_stats, fetch_recent_notes

router = APIRouter(prefix="/xhs", tags=["小红书数据"])


@router.get("/account", summary="获取小红书账号数据")
async def get_xhs_account():
    """
    获取小红书账号基本信息和统计数据
    """
    stats = await fetch_account_stats()
    
    if not stats:
        return {
            "code": 200,
            "data": None,
            "message": "无法获取账号数据，请检查MCP服务配置",
        }
    
    return {
        "code": 200,
        "data": stats,
        "message": "success"
    }


@router.get("/notes", summary="获取小红书笔记列表")
async def get_xhs_notes(limit: int = 10):
    """
    获取小红书最近发布的笔记列表及互动数据
    
    Args:
        limit: 获取笔记数量（默认10条）
    """
    notes = await fetch_recent_notes(limit=limit)
    
    return {
        "code": 200,
        "data": {
            "items": notes,
            "total": len(notes)
        },
        "message": "success"
    }


# 缓存数据
_cached_stats = None
_cache_time = 0
_CACHE_TTL = 300  # 5分钟缓存

# 强制清空缓存（部署时重置）
import os
if os.getenv("RESET_XHS_CACHE", "false").lower() == "true":
    _cached_stats = None
    _cache_time = 0


@router.get("/stats", summary="获取综合统计数据")
async def get_xhs_stats(force_refresh: bool = False):
    """
    获取小红书账号综合统计数据（用于Dashboard展示）
    
    Args:
        force_refresh: 是否强制刷新缓存
    """
    import time
    from app.services.xhs_crawler import _cached_account_stats as crawler_cache
    global _cached_stats, _cache_time
    
    # 检查API级别缓存（除非强制刷新）
    if not force_refresh and _cached_stats and (time.time() - _cache_time) < _CACHE_TTL:
        print(f"[XHS API] 使用API缓存数据: {_cached_stats.get('nickname')}")
        return {
            "code": 200,
            "data": _cached_stats,
            "message": "success"
        }
    
    # 调用MCP获取真实账号数据
    account = await fetch_account_stats()
    
    # 检查数据有效性
    is_valid_account = account and account.get("nickname") and account.get("nickname") not in ["xiaohongshu-mcp", "小红书账号", ""]
    
    if not is_valid_account:
        # 尝试使用缓存数据
        if _cached_stats and _cached_stats.get("nickname") and _cached_stats.get("nickname") not in ["xiaohongshu-mcp", "小红书账号", ""]:
            print(f"[XHS API] MCP获取失败，使用API缓存: {_cached_stats.get('nickname')}")
            return {
                "code": 200,
                "data": _cached_stats,
                "message": "使用缓存数据"
            }
        
        # 尝试使用crawler缓存
        if crawler_cache and crawler_cache.get("nickname") and crawler_cache.get("nickname") not in ["xiaohongshu-mcp", "小红书账号", ""]:
            _cached_stats = crawler_cache
            _cache_time = time.time()
            print(f"[XHS API] MCP获取失败，使用crawler缓存: {crawler_cache.get('nickname')}")
            return {
                "code": 200,
                "data": _cached_stats,
                "message": "使用缓存数据"
            }
        
        # 没有可用数据
        print("[XHS API] MCP无法获取账号数据，且无有效缓存")
        return {
            "code": 503,
            "data": None,
            "message": "无法获取账号数据，请检查MCP服务是否正常运行"
        }
    
    # 使用MCP获取的真实数据
    result = {
        "followers": account.get("followers", 0),
        "total_notes": account.get("total_notes", 0),
        "total_likes": account.get("total_likes", 0),
        "avg_engagement": 0,
        "recent_notes": [],
        "nickname": account.get("nickname", ""),
        "avatar": account.get("avatar", "")
    }
    
    # 更新API级别缓存
    _cached_stats = result
    _cache_time = time.time()
    print(f"[XHS API] MCP数据已更新并缓存: {result['nickname']}")
    
    return {
        "code": 200,
        "data": result,
        "message": "success"
    }


@router.post("/stats/refresh", summary="强制刷新账号数据")
async def refresh_xhs_stats():
    """
    强制刷新小红书账号数据缓存
    """
    import time
    from app.services.xhs_crawler import _cached_account_stats as crawler_cache
    global _cached_stats, _cache_time
    
    # 保存旧缓存，以防刷新失败
    old_cache = _cached_stats
    
    # 清除API级别缓存
    _cached_stats = None
    _cache_time = 0
    
    try:
        # 重新获取
        account = await fetch_account_stats()
        
        # 检查数据有效性
        is_valid = account and account.get("nickname") and account.get("nickname") not in ["xiaohongshu-mcp", "小红书账号", ""]
        
        if is_valid:
            result = {
                "followers": account.get("followers", 0),
                "total_notes": account.get("total_notes", 0),
                "total_likes": account.get("total_likes", 0),
                "avg_engagement": 0,
                "recent_notes": [],
                "nickname": account.get("nickname", ""),
                "avatar": account.get("avatar", "")
            }
            
            # 更新API级别缓存
            _cached_stats = result
            _cache_time = time.time()
            print(f"[XHS API] MCP数据已刷新: {result['nickname']}")
            
            return {
                "code": 200,
                "data": result,
                "message": "数据已刷新"
            }
    except Exception as e:
        print(f"[XHS API] 刷新时发生异常: {e}")
    
    # 刷新失败，尝试恢复缓存
    if old_cache and old_cache.get("nickname") and old_cache.get("nickname") not in ["xiaohongshu-mcp", "小红书账号", ""]:
        _cached_stats = old_cache
        _cache_time = time.time()
        print(f"[XHS API] 刷新失败，恢复旧缓存: {old_cache.get('nickname')}")
        return {
            "code": 200,
            "data": _cached_stats,
            "message": "使用缓存数据"
        }
    
    if crawler_cache and crawler_cache.get("nickname") and crawler_cache.get("nickname") not in ["xiaohongshu-mcp", "小红书账号", ""]:
        _cached_stats = crawler_cache
        _cache_time = time.time()
        print(f"[XHS API] 刷新失败，使用crawler缓存: {crawler_cache.get('nickname')}")
        return {
            "code": 200,
            "data": _cached_stats,
            "message": "使用缓存数据"
        }
    
    return {
        "code": 503,
        "data": None,
        "message": "刷新失败，无法获取账号数据"
    }


@router.get("/note/{note_id}", summary="获取笔记详情")
async def get_note_detail(note_id: str):
    """
    获取单条笔记的详细数据
    """
    notes = await fetch_recent_notes(limit=50)
    
    # 从列表中查找
    for note in notes:
        if note.get("note_id") == note_id:
            return {
                "code": 200,
                "data": note,
                "message": "success"
            }
    
    raise HTTPException(status_code=404, detail="笔记不存在")

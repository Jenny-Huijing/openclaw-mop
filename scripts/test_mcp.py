#!/usr/bin/env python3
"""
小红书 MCP 完整测试脚本
验证运营平台与 xiaohongshu-mcp 服务的连接

使用方法:
  cd /Users/irvinglu/.openclaw/workspace/xhs_platform/backend
  python3 ../scripts/test_mcp.py
"""

import asyncio
import sys
import os

# 添加backend到路径
backend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend")
sys.path.insert(0, backend_path)

from app.core.config import settings
from app.services.xhs_mcp import check_mcp_health, get_mcp_client, fetch_recent_notes_via_mcp


async def test_mcp_connection():
    """测试 MCP 连接"""
    print("=" * 60)
    print("🧪 小红书 MCP 接入测试")
    print("=" * 60)
    
    # 1. 检查配置
    print("\n📋 配置检查:")
    print(f"  MCP_URL: {settings.MCP_URL}")
    print(f"  MCP_ENABLED: {settings.MCP_ENABLED}")
    
    if not settings.MCP_ENABLED:
        print("\n❌ MCP 服务未启用，请在 .env 中设置 MCP_ENABLED=true")
        return False
    
    # 2. 健康检查
    print("\n💓 MCP 服务健康检查...")
    health = await check_mcp_health()
    if health.get("healthy"):
        print(f"  ✅ MCP 服务正常!")
        print(f"     Session ID: {health.get('session_id')}")
    else:
        print(f"  ❌ MCP 服务异常: {health.get('error')}")
        return False
    
    # 3. 检查登录状态
    print("\n👤 检查登录状态...")
    client = get_mcp_client()
    login_status = await client.check_login_status()
    if login_status.get("logged_in"):
        print(f"  ✅ 已登录")
        print(f"     用户名: {login_status.get('username', '未知')}")
    else:
        print(f"  ⚠️  未登录: {login_status.get('error', '请配置 Cookie')}")
    
    # 4. 测试获取笔记列表
    print("\n📝 测试获取推荐内容...")
    try:
        notes = await fetch_recent_notes_via_mcp(limit=5)
        if notes:
            print(f"  ✅ 成功! 获取到 {len(notes)} 条内容")
            for i, note in enumerate(notes[:3], 1):
                print(f"     {i}. {note.get('title', '无标题')[:35]}... "
                      f"({note.get('likes', 0)}👍 {note.get('comments', 0)}💬)")
        else:
            print("  ⚠️  未获取到内容")
    except Exception as e:
        print(f"  ❌ 失败: {e}")
    
    # 5. 测试搜索功能
    print("\n🔍 测试搜索功能 (关键词: 美食)...")
    try:
        results = await client.search_notes("美食", limit=3)
        if results:
            print(f"  ✅ 成功! 找到 {len(results)} 条结果")
            for i, r in enumerate(results[:3], 1):
                print(f"     {i}. {r.get('title', '无标题')[:35]}...")
        else:
            print("  ⚠️  未找到结果")
    except Exception as e:
        print(f"  ❌ 失败: {e}")
    
    print("\n" + "=" * 60)
    print("✨ 测试完成!")
    print("=" * 60)
    return True


async def show_mcp_tools():
    """显示可用的 MCP 工具"""
    print("\n🔧 可用的 MCP 工具 (13个):")
    tools = [
        ("check_login_status", "检查登录状态"),
        ("delete_cookies", "删除 Cookies"),
        ("favorite_feed", "收藏帖子"),
        ("get_feed_detail", "获取帖子详情"),
        ("get_login_qrcode", "获取登录二维码"),
        ("like_feed", "点赞帖子"),
        ("list_feeds", "获取推荐列表"),
        ("post_comment_to_feed", "发表评论"),
        ("publish_content", "发布图文内容"),
        ("publish_with_video", "发布视频内容"),
        ("reply_comment_in_feed", "回复评论"),
        ("search_feeds", "搜索帖子"),
        ("user_profile", "获取用户资料"),
    ]
    for name, desc in tools:
        print(f"  • {name:25s} - {desc}")


if __name__ == "__main__":
    try:
        result = asyncio.run(test_mcp_connection())
        asyncio.run(show_mcp_tools())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n🛑 测试已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

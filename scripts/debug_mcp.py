#!/usr/bin/env python3
"""
小红书 MCP 调试脚本
使用底层 HTTP 连接来测试 MCP 工具调用
"""

import asyncio
import json
import sys
import os

# 添加backend到路径
backend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend")
sys.path.insert(0, backend_path)

import aiohttp


async def test_mcp_with_session():
    """使用同一个 session 测试 MCP 调用"""
    
    print("=" * 60)
    print("🔧 小红书 MCP 调试工具")
    print("=" * 60)
    
    mcp_url = "http://localhost:18060/mcp"
    
    # 创建单个 session 用于所有请求
    async with aiohttp.ClientSession() as session:
        
        # 1. Initialize
        print("\n1️⃣ 初始化 MCP 会话...")
        init_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "xhs-platform", "version": "1.0.0"}
            }
        }
        
        async with session.post(mcp_url, json=init_payload) as resp:
            init_result = await resp.json()
            print(f"   初始化: {'✅ 成功' if 'result' in init_result else '❌ 失败'}")
            if 'result' in init_result:
                server_info = init_result['result'].get('serverInfo', {})
                print(f"   服务器: {server_info.get('name')} v{server_info.get('version')}")
        
        # 2. Send initialized notification
        print("\n2️⃣ 发送 initialized 通知...")
        init_notify = {
            "jsonrpc": "2.0",
            "method": "initialized",
            "params": {}
        }
        async with session.post(mcp_url, json=init_notify) as resp:
            # notification 不需要响应
            print(f"   状态: {resp.status}")
        
        # 3. List Tools
        print("\n3️⃣ 获取工具列表...")
        list_tools = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        async with session.post(mcp_url, json=list_tools) as resp:
            tools_result = await resp.json()
            if 'result' in tools_result:
                tools = tools_result['result'].get('tools', [])
                print(f"   发现 {len(tools)} 个工具:")
                for tool in tools:
                    print(f"     • {tool.get('name')}: {tool.get('description', '无描述')[:50]}")
            else:
                print(f"   错误: {tools_result.get('error', {}).get('message', '未知错误')}")
        
        # 4. Call check_login_status
        print("\n4️⃣ 调用 check_login_status...")
        call_tool = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "check_login_status",
                "arguments": {}
            }
        }
        async with session.post(mcp_url, json=call_tool) as resp:
            call_result = await resp.json()
            print(f"   响应: {json.dumps(call_result, indent=2, ensure_ascii=False)[:500]}")
        
        # 5. Call list_feeds
        print("\n5️⃣ 调用 list_feeds...")
        call_feeds = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "list_feeds",
                "arguments": {}
            }
        }
        async with session.post(mcp_url, json=call_feeds) as resp:
            feeds_result = await resp.json()
            if 'result' in feeds_result:
                content = feeds_result['result'].get('content', [])
                if content:
                    try:
                        data = json.loads(content[0].get('text', '{}'))
                        feeds = data.get('feeds', [])
                        print(f"   获取到 {len(feeds)} 条推荐内容")
                        for i, feed in enumerate(feeds[:3], 1):
                            print(f"     {i}. {feed.get('title', '无标题')[:40]}...")
                    except Exception as e:
                        print(f"   解析错误: {e}")
            else:
                print(f"   错误: {feeds_result.get('error', {}).get('message', '未知错误')}")
    
    print("\n" + "=" * 60)
    print("✨ 调试完成")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(test_mcp_with_session())
    except KeyboardInterrupt:
        print("\n\n🛑 已取消")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()

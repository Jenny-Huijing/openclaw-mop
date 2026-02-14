"""
飞书消息推送服务
使用飞书群机器人 Webhook 发送消息
"""
import os
import json
import aiohttp
from datetime import datetime

FEISHU_WEBHOOK_URL = os.getenv("FEISHU_WEBHOOK_URL", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost")

async def send_feishu_message(content: dict, title: str = "系统通知"):
    """
    发送飞书消息
    
    参数:
        content: 消息内容字典
        title: 消息标题
    """
    if not FEISHU_WEBHOOK_URL:
        print("[Feishu] 未配置飞书 Webhook URL，跳过发送")
        return False
    
    try:
        message = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": title
                    },
                    "template": "blue"
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": format_content(content)
                        }
                    }
                ]
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                FEISHU_WEBHOOK_URL,
                json=message,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("code") == 0:
                        print("[Feishu] 消息发送成功")
                        return True
                    else:
                        print(f"[Feishu] 消息发送失败: {result}")
                        return False
                else:
                    print(f"[Feishu] HTTP 错误: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"[Feishu] 发送消息异常: {e}")
        return False


def format_content(content: dict) -> str:
    """格式化消息内容"""
    lines = []
    for key, value in content.items():
        if value:
            lines.append(f"**{key}:** {value}")
    return "\n".join(lines)


async def send_review_notification(
    content_id: str,
    title: str,
    preview: str,
    created_at: str
):
    """
    发送内容审核提醒
    
    参数:
        content_id: 内容ID
        title: 内容标题
        preview: 内容预览
        created_at: 创建时间
    """
    review_url = f"{FRONTEND_URL}/content/{content_id}"
    
    message_content = {
        "📋 状态": "内容创作完成，等待审核",
        "📝 标题": title[:50] + "..." if len(title) > 50 else title,
        "👀 预览": preview[:100] + "..." if len(preview) > 100 else preview,
        "⏰ 时间": created_at,
        "🔗 链接": f"[点击审核]({review_url})"
    }
    
    return await send_feishu_message(
        content=message_content,
        title="🤖 新媒体智能运营平台 - 内容审核提醒"
    )


async def send_publish_notification(
    content_id: str,
    title: str,
    status: str,
    published_at: str = None
):
    """
    发送内容发布通知
    
    参数:
        content_id: 内容ID
        title: 内容标题
        status: 发布状态（成功/失败）
        published_at: 发布时间
    """
    status_icon = "✅" if status == "success" else "❌"
    status_text = "发布成功" if status == "success" else "发布失败"
    
    message_content = {
        "📋 状态": f"{status_icon} {status_text}",
        "📝 标题": title[:50] + "..." if len(title) > 50 else title,
        "⏰ 时间": published_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return await send_feishu_message(
        content=message_content,
        title=f"🤖 新媒体智能运营平台 - 内容发布通知"
    )

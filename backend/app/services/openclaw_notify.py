"""
OpenClaw 通知服务
当平台有重要事件时，通知 OpenClaw (小珑宝)
"""
import os
import json
import aiohttp
from datetime import datetime

# OpenClaw Gateway 配置
OPENCLAW_GATEWAY_URL = os.getenv("OPENCLAW_GATEWAY_URL", "http://host.docker.internal:3000")
OPENCLAW_TARGET_LABEL = os.getenv("OPENCLAW_TARGET_LABEL", "default")


async def notify_openclaw(event_type: str, payload: dict):
    """
    通知 OpenClaw (小珑宝)
    
    参数:
        event_type: 事件类型 (content_review, publish_success, etc.)
        payload: 事件数据
    """
    # 构建通知消息
    message = f"""
🐾 **小珑宝收到平台通知**

📋 事件: {event_type}
⏰ 时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
📦 数据: {json.dumps(payload, ensure_ascii=False, indent=2)}

请处理这条通知！
"""
    
    # 尝试多种方式通知 OpenClaw
    
    # 方式1: 通过 HTTP API 调用 (如果 OpenClaw 提供了 webhook 端点)
    # 方式2: 写入共享文件，OpenClaw 定时读取
    # 方式3: 通过数据库/Redis 队列
    
    # 目前使用方式2: 写入通知文件
    try:
        await _write_notification_file(event_type, payload)
        print(f"[OpenClaw Notify] 通知已写入: {event_type}")
        return True
    except Exception as e:
        print(f"[OpenClaw Notify] 通知失败: {e}")
        return False


async def _write_notification_file(event_type: str, payload: dict):
    """将通知写入文件，OpenClaw 会定时检查"""
    import os
    from pathlib import Path
    
    # 通知目录 - 支持Docker和本地开发环境
    # 本地开发: 使用相对于workspace的路径
    # Docker: 使用 /app/data/notifications
    if os.path.exists("/app/data"):
        notify_dir = "/app/data/notifications"
    else:
        # 本地开发环境
        workspace_dir = Path(__file__).parent.parent.parent.parent  # backend的上级目录
        notify_dir = str(workspace_dir / "backend" / "data" / "notifications")
    
    os.makedirs(notify_dir, exist_ok=True)
    
    # 文件名: openclaw_notify_{timestamp}_{event_type}.json
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"openclaw_notify_{timestamp}_{event_type}.json"
    filepath = os.path.join(notify_dir, filename)
    
    notification = {
        "event_type": event_type,
        "timestamp": datetime.now().isoformat(),
        "payload": payload
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(notification, f, ensure_ascii=False, indent=2)
    
    print(f"[OpenClaw Notify] 文件已创建: {filepath}")


async def notify_content_review(
    content_id: str,
    title: str,
    preview: str,
    workflow_id: str = None
):
    """
    通知 OpenClaw 有内容需要审核
    
    参数:
        content_id: 内容ID
        title: 内容标题
        preview: 内容预览
        workflow_id: 工作流ID
    """
    payload = {
        "content_id": content_id,
        "title": title,
        "preview": preview[:500],  # 限制长度
        "workflow_id": workflow_id,
        "action_required": "review",  # 需要审核
        "frontend_url": f"/content/{content_id}"
    }
    
    return await notify_openclaw("content_review", payload)


async def notify_content_published(
    content_id: str,
    title: str,
    status: str,
    error: str = None
):
    """通知 OpenClaw 内容已发布"""
    payload = {
        "content_id": content_id,
        "title": title,
        "status": status,  # success / failed
        "error": error
    }
    
    return await notify_openclaw("content_published", payload)

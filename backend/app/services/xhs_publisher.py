"""
小红书内容发布服务
集成 MCP 的 publish_content 工具
"""

import os
import re
from typing import Optional, List
from app.core.config import settings
from app.services.xhs_mcp import get_mcp_client


class XHSPublisher:
    """小红书内容发布器"""
    
    def __init__(self):
        self.mcp_client = get_mcp_client()
    
    async def publish_note(
        self,
        title: str,
        content: str,
        images: List[str],
        tags: Optional[List[str]] = None,
        schedule_at: Optional[str] = None
    ) -> dict:
        """
        发布小红书图文笔记
        
        Args:
            title: 标题（最多20个中文字）
            content: 正文内容（不包含 # 标签）
            images: 图片路径列表（HTTP链接或本地路径）
            tags: 话题标签列表
            schedule_at: 定时发布时间（ISO8601格式）
        
        Returns:
            {"success": True, "note_id": "xxx", "url": "xxx"}
            {"success": False, "error": "xxx"}
        """
        try:
            # 清理内容中的 # 标签（MCP 要求用 tags 参数）
            clean_content = re.sub(r'#([^#\s]+)#?', r'\1', content)
            
            # 限制标题长度（20个中文字）
            if len(title) > 20:
                title = title[:20]
            
            # 转换图片路径为 MCP 可访问的路径
            mcp_images = self._convert_image_paths(images)
            
            print(f"[Publish] 准备发布，图片数量: {len(mcp_images)}")
            for i, img in enumerate(mcp_images):
                print(f"  图片{i+1}: {img[:60]}...")
            
            # 调用 MCP 发布
            params = {
                "title": title,
                "content": clean_content,
                "images": mcp_images,
                "tags": tags or []
            }
            # 只有设置了定时发布时才添加 schedule_at
            if schedule_at:
                params["schedule_at"] = schedule_at
            
            result = await self.mcp_client._call_tool("publish_content", params)
            
            if "error" in result:
                return {
                    "success": False,
                    "error": result["error"]
                }
            
            # 解析返回结果
            content_list = result.get("result", {}).get("content", [])
            if content_list:
                import json
                data = json.loads(content_list[0].get("text", "{}"))
                return {
                    "success": True,
                    "note_id": data.get("note_id"),
                    "url": data.get("url"),
                    "message": "发布成功"
                }
            
            return {
                "success": False,
                "error": "返回数据为空"
            }
            
        except Exception as e:
            import traceback
            return {
                "success": False,
                "error": f"{str(e)}\n{traceback.format_exc()}"
            }
    
    def _convert_image_paths(self, images: List[str]) -> List[str]:
        """
        转换图片路径为 MCP 可访问的路径
        
        规则：
        1. HTTP/HTTPS URL: 直接使用
        2. /static/images/xxx: 转换为 /app/data/images/xxx (MCP挂载目录)
        3. 本地绝对路径: 检查是否在挂载目录内
        """
        converted = []
        
        for img in images:
            if not img:
                continue
                
            # HTTP URL 直接使用
            if img.startswith('http://') or img.startswith('https://'):
                converted.append(img)
                continue
            
            # /static/images/xxx 转换为 MCP 挂载路径
            if img.startswith('/static/images/'):
                filename = os.path.basename(img)
                # MCP 容器挂载: ./mcp/data:/app/data
                mcp_path = f"/app/data/images/{filename}"
                converted.append(mcp_path)
                continue
            
            # 其他路径原样使用（假设是绝对路径）
            converted.append(img)
        
        return converted
    
    async def publish_with_content_images(
        self,
        title: str,
        content: str,
        content_images: List[dict],
        tags: Optional[List[str]] = None,
        schedule_at: Optional[str] = None
    ) -> dict:
        """
        使用内容配图发布笔记
        
        Args:
            content_images: 内容配图列表 [{"url": "...", "local_path": "..."}, ...]
        """
        # 提取图片路径（优先使用本地路径）
        image_paths = []
        for img in content_images:
            if img.get("local_path"):
                image_paths.append(img["local_path"])
            elif img.get("url"):
                image_paths.append(img["url"])
        
        if not image_paths:
            return {
                "success": False,
                "error": "没有可用的配图"
            }
        
        return await self.publish_note(
            title=title,
            content=content,
            images=image_paths,
            tags=tags,
            schedule_at=schedule_at
        )


# 单例
_publisher = None

def get_publisher() -> XHSPublisher:
    """获取发布器实例"""
    global _publisher
    if _publisher is None:
        _publisher = XHSPublisher()
    return _publisher

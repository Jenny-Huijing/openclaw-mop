"""
图像生成服务 - 支持方舟 Seedream 模型
"""

import os
import base64
import uuid
from datetime import datetime
from typing import Optional, List
import httpx
import asyncio

# 方舟配置
try:
    from app.core.config import settings
    ARK_API_KEY = settings.ARK_API_KEY or os.getenv("ARK_API_KEY", "")
    ARK_IMAGE_ENDPOINT = settings.ARK_IMAGE_ENDPOINT or os.getenv("ARK_IMAGE_ENDPOINT", "")
except ImportError:
    ARK_API_KEY = os.getenv("ARK_API_KEY", "")
    ARK_IMAGE_ENDPOINT = os.getenv("ARK_IMAGE_ENDPOINT", "")

ARK_BASE_URL = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")

# 图片存储路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
IMAGE_STORAGE_PATH = os.getenv("IMAGE_STORAGE_PATH", os.path.join(BASE_DIR, "static", "images"))


class ImageGenerationService:
    """图像生成服务"""
    
    def __init__(self):
        self.api_key = ARK_API_KEY
        self.endpoint = ARK_IMAGE_ENDPOINT
        self.base_url = ARK_BASE_URL
        self.enabled = bool(self.api_key and self.endpoint)
        
        # 确保存储目录存在
        os.makedirs(IMAGE_STORAGE_PATH, exist_ok=True)
    
    async def _generate_single_image(
        self, 
        prompt: str, 
        idx: int,
        content_id: str,
        width: int,
        height: int
    ) -> dict:
        """生成单张图片"""
        try:
            print(f"[Image] 生成图片 {idx+1}: {prompt[:50]}...")
            
            # 调用方舟图像生成 API
            image_url = await self._call_ark_image_api(
                prompt=prompt,
                width=width,
                height=height
            )
            
            if image_url:
                # 下载并保存图片
                local_path = await self._download_image(
                    image_url, 
                    f"{content_id}_{idx}_{uuid.uuid4().hex[:8]}.png"
                )
                
                return {
                    "prompt": prompt,
                    "url": image_url,
                    "local_path": local_path,
                    "status": "success"
                }
            else:
                return {
                    "prompt": prompt,
                    "url": None,
                    "local_path": None,
                    "status": "failed",
                    "error": "API 返回空"
                }
                
        except Exception as e:
            print(f"[Image] 生成失败: {e}")
            return {
                "prompt": prompt,
                "url": None,
                "local_path": None,
                "status": "failed",
                "error": str(e)
            }
    
    async def generate_images(
        self, 
        prompts: List[str], 
        content_id: str,
        width: int = 1024,
        height: int = 1024
    ) -> List[dict]:
        """
        根据提示词并行生成图片
        
        Args:
            prompts: 图片提示词列表
            content_id: 内容ID，用于关联
            width: 图片宽度
            height: 图片高度
        
        Returns:
            [{"prompt": str, "url": str, "local_path": str}, ...]
        """
        if not self.enabled:
            print("[Image] 图像生成功能未启用，缺少 ARK_API_KEY 或 ARK_IMAGE_ENDPOINT")
            return []
        
        print(f"[Image] 开始并行生成 {len(prompts)} 张图片...")
        
        # 并行生成所有图片
        tasks = [
            self._generate_single_image(prompt, idx, content_id, width, height)
            for idx, prompt in enumerate(prompts)
        ]
        
        results = await asyncio.gather(*tasks)
        
        success_count = sum(1 for r in results if r["status"] == "success")
        print(f"[Image] 图片生成完成: {success_count}/{len(prompts)} 成功")
        
        return results
    
    async def _call_ark_image_api(
        self, 
        prompt: str, 
        width: int = 1024, 
        height: int = 1024
    ) -> Optional[str]:
        """调用方舟图像生成 API"""
        
        url = f"{self.base_url}/images/generations"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.endpoint,
            "prompt": prompt,
            "width": width,
            "height": height,
            "seed": -1,  # 随机种子
            "watermark": False
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            # 方舟返回的是 base64 或 URL
            if "data" in data and len(data["data"]) > 0:
                image_data = data["data"][0]
                
                # 如果有 URL 直接返回
                if "url" in image_data:
                    return image_data["url"]
                
                # 如果是 base64，保存到本地
                if "b64_json" in image_data:
                    return await self._save_base64_image(image_data["b64_json"])
            
            return None
    
    async def _download_image(self, image_url: str, filename: str) -> str:
        """下载图片到本地"""
        local_path = os.path.join(IMAGE_STORAGE_PATH, filename)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(image_url)
            response.raise_for_status()
            
            with open(local_path, "wb") as f:
                f.write(response.content)
        
        return f"/static/images/{filename}"
    
    async def _save_base64_image(self, b64_data: str) -> str:
        """保存 base64 图片"""
        filename = f"{uuid.uuid4().hex}.png"
        local_path = os.path.join(IMAGE_STORAGE_PATH, filename)
        
        image_bytes = base64.b64decode(b64_data)
        with open(local_path, "wb") as f:
            f.write(image_bytes)
        
        return f"/static/images/{filename}"


# 单例实例
image_service = ImageGenerationService()

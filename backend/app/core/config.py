"""
新媒体智能运营平台 - 后端核心模块
"""

from typing import Optional
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    # 应用
    APP_NAME: str = "新媒体智能运营平台"
    DEBUG: bool = True
    API_KEY: str = "xhs_agent_internal_key"
    
    # 数据库 (使用 PostgreSQL)
    DATABASE_URL: str = "postgresql://postgres:postgres@postgres:5432/nmop"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # RabbitMQ
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    
    # Celery
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None
    
    # 搜索服务
    BRAVE_API_KEY: Optional[str] = None  # Brave Search API Key，用于实时热点搜索
    
    # 方舟大模型
    ARK_API_KEY: Optional[str] = None
    ARK_MODEL_ENDPOINT: Optional[str] = None  # 文本生成 (豆包)
    ARK_IMAGE_ENDPOINT: Optional[str] = None  # 图像生成 (即梦)
    
    # MCP 服务配置（小红书 MCP 服务）
    # 本地开发: http://localhost:18060/mcp
    # Docker环境: http://host.docker.internal:18060/mcp
    MCP_URL: str = "http://xiaohongshu-mcp:18060/mcp"
    MCP_ENABLED: bool = True  # 启用 MCP 服务
    
    # 小红书账号配置
    XHS_USER_ID: Optional[str] = None  # 用户ID，用于获取账号数据，从环境变量读取
    
    # 前端地址（用于飞书通知中的链接）
    FRONTEND_URL: str = "http://localhost"
    
    class Config:
        env_file = ".env"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.CELERY_BROKER_URL:
            self.CELERY_BROKER_URL = self.RABBITMQ_URL
        if not self.CELERY_RESULT_BACKEND:
            self.CELERY_RESULT_BACKEND = self.REDIS_URL


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

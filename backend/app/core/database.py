"""
数据库连接管理
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# 判断数据库类型
IS_SQLITE = settings.DATABASE_URL.startswith("sqlite")

if IS_SQLITE:
    # SQLite 配置
    # 同步引擎
    engine = create_engine(
        settings.DATABASE_URL.replace("sqlite+aiosqlite://", "sqlite://"),
        connect_args={"check_same_thread": False}
    )
    # 异步引擎
    async_engine = create_async_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL 配置
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )
    # 异步引擎（用于FastAPI）
    # 将 postgresql:// 替换为 postgresql+asyncpg://
    ASYNC_DATABASE_URL = settings.DATABASE_URL.replace(
        "postgresql://", "postgresql+asyncpg://"
    )
    async_engine = create_async_engine(
        ASYNC_DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )

# Session工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

# 导出 session maker 供后台任务使用
async_session_maker = AsyncSessionLocal


# 依赖注入用
async def get_db():
    """获取数据库会话（异步）"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_sync_db():
    """获取数据库会话（同步，用于Celery）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

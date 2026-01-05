"""
异步数据库连接配置
使用 SQLAlchemy 2.0 异步支持
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker, AsyncEngine
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator
from app.core.config import settings

# 异步数据库URL (需要改为 asyncpg 或 aiomysql 驱动)
# 例如: postgresql+asyncpg://user:password@localhost/dbname
# 或: mysql+aiomysql://user:password@localhost/dbname

# 创建异步数据库引擎
async_engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
                      .replace("mysql://", "mysql+aiomysql://", 1)
                      .replace("sqlite://", "sqlite+aiosqlite://", 1),
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=300,
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 创建基类
Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """异步数据库依赖"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """初始化数据库表"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """关闭数据库连接"""
    await async_engine.dispose()

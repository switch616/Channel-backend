from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.core.config import settings
from typing import AsyncGenerator

# 使用 .env 中的 DATABASE_URL
DATABASE_URL = settings.DATABASE_URL

# 创建异步引擎
engine = create_async_engine(DATABASE_URL, echo=False, future=True)

# 创建异步 session 工厂
async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# 声明基类
Base = declarative_base()

# 异步依赖注入
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

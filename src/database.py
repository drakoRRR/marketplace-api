from src.config import DATABASE_URL, REDIS_HOST
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from redis.asyncio import Redis


redis_conn = Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)

async_engine = create_async_engine(DATABASE_URL, future=True, echo=True)
async_session = sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async session"""
    session: AsyncSession = async_session()
    try:
        yield session
    finally:
        await session.close()


def custom_cache_key(func, *args, **kwargs):
    request = kwargs.get("request")
    key = request.url.path + "?" + "&".join([f"{k}={v}" for k, v in sorted(request.query_params.items())])
    return key

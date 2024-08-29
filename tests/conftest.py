import asyncio

import pytest

from passlib.hash import bcrypt

from src.auth.hashing import Hasher
from src.auth.models import User
from src.config import DATABASE_TEST_ASYNC_URL, DATABASE_TEST_SYNC_URL
from typing import AsyncGenerator
from httpx import AsyncClient

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

from src.main import fastapi_app
from src.database import Base, get_db


async_test_engine = create_async_engine(DATABASE_TEST_ASYNC_URL, future=True)
async_test_session = sessionmaker(async_test_engine, expire_on_commit=False, class_=AsyncSession)

sync_test_engine = create_engine(DATABASE_TEST_SYNC_URL, future=True)
sync_test_session = sessionmaker(autocommit=False, autoflush=False, bind=sync_test_engine)


USER_NAME = "john_junior"
EMAIL = "example@example.com"
PASSWORD = "qwerty1234"


# @pytest.fixture(scope="session", autouse=True)
# def test_db():
#     """Create and drop the test database tables."""
#     Base.metadata.create_all(bind=sync_test_engine)
#     try:
#         yield
#     finally:
#         Base.metadata.drop_all(bind=sync_test_engine)


async def test_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async session"""
    session: AsyncSession = async_test_session()
    try:
        yield session
    finally:
        await session.close()


@pytest.fixture(scope="session")
async def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def client():
    fastapi_app.dependency_overrides[get_db] = test_get_db
    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        yield client
    fastapi_app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def db_async_session():
    async with async_test_session() as session:
        yield session


@pytest.fixture(scope="function")
async def user(db_async_session: AsyncSession):
    result = await db_async_session.execute(select(User).filter_by(user_name=USER_NAME, email=EMAIL))
    existing_user = result.scalars().first()

    if existing_user:
        return existing_user

    hashed_password = Hasher.get_password_hash(PASSWORD)
    test_user = User(
        user_name=USER_NAME,
        email=EMAIL,
        hashed_password=hashed_password,
    )
    db_async_session.add(test_user)
    await db_async_session.commit()
    return test_user


@pytest.fixture(scope="function", autouse=True)
def clean_db():
    Base.metadata.create_all(bind=sync_test_engine)
    try:
        yield
    finally:
        Base.metadata.drop_all(bind=sync_test_engine)
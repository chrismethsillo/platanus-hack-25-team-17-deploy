"""Pytest configuration and fixtures."""

import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.database import Base
from app.main import app

# Test database URL (use a separate test database)
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/platanus_test_db"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests.

    Yields:
        Event loop instance
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine() -> AsyncGenerator[AsyncEngine]:
    """Create test database engine.

    Yields:
        AsyncEngine: Test database engine
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=False,  # Disable pre-ping to avoid event loop issues
        pool_size=1,  # Single connection to avoid conflicts
        max_overflow=0,
    )
    yield engine
    await engine.dispose()
    # Give time for connections to close
    await asyncio.sleep(0.1)


@pytest.fixture(scope="function")
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession]:
    """Create a test database session.

    Creates tables before each test and drops them after.

    Args:
        test_engine: Test database engine

    Yields:
        AsyncSession: Test database session
    """
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await test_engine.dispose(close=False)  # Ensure connection is released

    # Create session factory for this test
    TestSessionLocal = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    # Create session
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

    # Drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose(close=False)  # Ensure connection is released


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    """Create test client with database session override.

    Args:
        db_session: Test database session

    Yields:
        AsyncClient: Test HTTP client
    """
    from app.routers.deps import get_db

    async def override_get_db() -> AsyncGenerator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as test_client:
        yield test_client

    app.dependency_overrides.clear()

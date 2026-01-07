"""Shared test fixtures and configuration."""

import asyncio
from datetime import datetime
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.main import app
from src.db import get_db
from src.models.base import Base
from src.models.profile import Profile, ProfileStatus
from src.services.docker_service import DockerService
from src.services.adb_service import ADBService
from src.services.fingerprint_service import FingerprintService
from src.schemas.profile import DeviceFingerprint, ScreenConfig, ProxyConfig


# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def async_engine():
    """Create async engine for tests."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for tests."""
    async_session = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# Mock fixtures

@pytest.fixture
def mock_docker_client() -> MagicMock:
    """Mock Docker client."""
    mock = MagicMock()

    # Mock containers
    mock.containers.list.return_value = []
    mock.containers.get.return_value = MagicMock(
        id="test-container-id",
        name="mobiledroid-test",
        status="running",
        ports={"5555/tcp": [{"HostPort": "5555"}]},
    )
    mock.containers.run.return_value = MagicMock(
        id="test-container-id",
        name="mobiledroid-test",
    )

    # Mock networks
    mock.networks.get.return_value = MagicMock()
    mock.networks.create.return_value = MagicMock()

    return mock


@pytest.fixture
def mock_fingerprint_service() -> MagicMock:
    """Mock fingerprint service."""
    mock = MagicMock(spec=FingerprintService)
    mock.fingerprint_to_env.return_value = {
        "DEVICE_MODEL": "Pixel 7",
        "DEVICE_BRAND": "google",
        "DEVICE_MANUFACTURER": "Google",
        "DEVICE_WIDTH": "1080",
        "DEVICE_HEIGHT": "2400",
        "DEVICE_DPI": "420",
    }
    mock.get_all_fingerprints.return_value = [
        {
            "id": "pixel-7",
            "name": "Google Pixel 7",
            "model": "Pixel 7",
            "brand": "google",
            "manufacturer": "Google",
        }
    ]
    return mock


@pytest.fixture
def mock_docker_service(mock_docker_client, mock_fingerprint_service) -> MagicMock:
    """Mock Docker service."""
    mock = MagicMock(spec=DockerService)
    mock.client = mock_docker_client
    mock.fingerprint_service = mock_fingerprint_service

    # Async method mocks
    mock.create_container = AsyncMock(return_value=("test-container-id", 5555))
    mock.start_container = AsyncMock(return_value=True)
    mock.stop_container = AsyncMock(return_value=True)
    mock.remove_container = AsyncMock(return_value=True)
    mock.wait_for_boot = AsyncMock(return_value=True)
    mock.get_container_status.return_value = "running"
    mock.get_container_logs.return_value = "Boot completed"
    mock.list_containers.return_value = []

    return mock


@pytest.fixture
def mock_adb_service() -> MagicMock:
    """Mock ADB service."""
    mock = MagicMock(spec=ADBService)
    mock._devices = {}

    # Async method mocks
    mock.connect = AsyncMock(return_value=True)
    mock.disconnect = AsyncMock(return_value=True)
    mock.screenshot = AsyncMock(return_value=b"fake-png-data")
    mock.screenshot_base64 = AsyncMock(return_value="ZmFrZS1wbmctZGF0YQ==")
    mock.tap = AsyncMock(return_value=True)
    mock.swipe = AsyncMock(return_value=True)
    mock.input_text = AsyncMock(return_value=True)
    mock.press_key = AsyncMock(return_value=True)
    mock.press_back = AsyncMock(return_value=True)
    mock.press_home = AsyncMock(return_value=True)
    mock.press_enter = AsyncMock(return_value=True)
    mock.get_ui_hierarchy = AsyncMock(return_value="<hierarchy>...</hierarchy>")
    mock.shell = AsyncMock(return_value="shell output")
    mock.get_device_info = AsyncMock(return_value={
        "model": "Pixel 7",
        "brand": "google",
        "manufacturer": "Google",
        "android_version": "14",
        "sdk_version": "34",
        "fingerprint": "google/panther/panther:14/...",
    })
    mock.install_apk = AsyncMock(return_value=True)
    mock.launch_app = AsyncMock(return_value=True)

    return mock


# Sample data fixtures

@pytest.fixture
def sample_fingerprint() -> DeviceFingerprint:
    """Sample device fingerprint."""
    return DeviceFingerprint(
        model="Pixel 7",
        brand="google",
        manufacturer="Google",
        build_fingerprint="google/panther/panther:14/UP1A.231005.007/10754064:user/release-keys",
        android_version="14",
        sdk_version="34",
        hardware="panther",
        board="panther",
        product="panther",
        screen=ScreenConfig(width=1080, height=2400, dpi=420),
        timezone="America/New_York",
        locale="en_US",
    )


@pytest.fixture
def sample_proxy() -> ProxyConfig:
    """Sample proxy configuration."""
    return ProxyConfig(
        type="http",
        host="proxy.example.com",
        port=8080,
        username="user",
        password="pass",
    )


@pytest.fixture
def sample_profile_data(sample_fingerprint, sample_proxy) -> dict:
    """Sample profile creation data."""
    return {
        "name": "Test Profile",
        "fingerprint": sample_fingerprint.model_dump(),
        "proxy": sample_proxy.model_dump(),
    }


@pytest_asyncio.fixture
async def sample_profile(db_session: AsyncSession, sample_fingerprint, sample_proxy) -> Profile:
    """Create a sample profile in the database."""
    profile = Profile(
        id="test-profile-id",
        name="Test Profile",
        fingerprint=sample_fingerprint.model_dump(),
        proxy=sample_proxy.model_dump(),
        status=ProfileStatus.STOPPED,
        container_id=None,
        adb_port=None,
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(profile)
    return profile


@pytest_asyncio.fixture
async def running_profile(db_session: AsyncSession, sample_fingerprint, sample_proxy) -> Profile:
    """Create a running profile in the database."""
    profile = Profile(
        id="running-profile-id",
        name="Running Profile",
        fingerprint=sample_fingerprint.model_dump(),
        proxy=sample_proxy.model_dump(),
        status=ProfileStatus.RUNNING,
        container_id="running-container-id",
        adb_port=5555,
        last_started_at=datetime.utcnow(),
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(profile)
    return profile

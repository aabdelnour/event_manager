import asyncio
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from faker import Faker
from app.main import app
from app.database import Base
from app.models.user_model import User, UserRole
from app.dependencies import get_db, get_settings
from app.utils.security import hash_password
from datetime import datetime
import uuid
from unittest.mock import AsyncMock


fake = Faker()
settings = get_settings()
TEST_DATABASE_URL = str(settings.database_url).replace("postgresql://", "postgresql+asyncpg://")
engine = create_async_engine(TEST_DATABASE_URL, echo=settings.debug)
AsyncTestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_email_service(mocker):
    mock = AsyncMock()
    mocker.patch('app.services.email_service.EmailService.send_verification_email', mock)
    return mock

@pytest.fixture(scope="session")
async def initialize_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function")
async def db_session():
    async with AsyncTestingSessionLocal() as session:
        yield session
        await session.rollback()

@pytest.fixture(scope="function")
async def async_client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
async def user(db_session):
    user_data = {
        "nickname": fake.user_name(),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": f"test_{uuid.uuid4()}@example.com",
        "hashed_password": hash_password("MySuperPassword$1234"),
        "role": UserRole.AUTHENTICATED,
        "email_verified": False,
        "is_locked": False,
    }
    user = User(**user_data)
    db_session.add(user)
    await db_session.commit()
    yield user
    await db_session.delete(user)
    await db_session.commit()

@pytest.fixture(scope="function")
async def verified_user(db_session):
    user_data = {
        "nickname": fake.user_name(),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": f"verified_{uuid.uuid4()}@example.com",
        "hashed_password": hash_password("VerifiedPassword123!"),
        "role": UserRole.AUTHENTICATED,
        "email_verified": True,
        "is_locked": False,
    }
    user = User(**user_data)
    db_session.add(user)
    await db_session.commit()
    yield user
    await db_session.delete(user)
    await db_session.commit()

@pytest.fixture(scope="function")
async def admin_user(db_session):
    user_data = {
        "nickname": f"admin_user_{uuid.uuid4()}",
        "email": f"admin_{uuid.uuid4()}@example.com",
        "first_name": "Admin",
        "last_name": "User",
        "hashed_password": hash_password("securepassword"),
        "role": UserRole.ADMIN,
        "is_locked": False,
        "email_verified": True
    }
    user = User(**user_data)
    db_session.add(user)
    await db_session.commit()
    yield user
    await db_session.delete(user)
    await db_session.commit()

@pytest.fixture(scope="function")
async def manager_user(db_session):
    user = User(
        nickname=f"manager_john_{uuid.uuid4()}",
        first_name="John",
        last_name="Doe",
        email=f"manager_user_{uuid.uuid4()}@example.com",
        hashed_password=hash_password("securepassword"),
        role=UserRole.MANAGER,
        is_locked=False,
        email_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    yield user
    await db_session.delete(user)
    await db_session.commit()

@pytest.fixture(scope="function")
async def admin_token(async_client, admin_user):
    login_data = {"username": admin_user.email, "password": "securepassword"}
    response = await async_client.post("/token", data=login_data)
    return response.json()["access_token"]

@pytest.fixture(scope="function")
async def user_token(async_client, verified_user):
    login_data = {"username": verified_user.email, "password": "VerifiedPassword123!"}
    response = await async_client.post("/token", data=login_data)
    return response.json()["access_token"]

@pytest.fixture(scope="function")
async def manager_token(async_client, manager_user):
    login_data = {"username": manager_user.email, "password": "securepassword"}
    response = await async_client.post("/token", data=login_data)
    return response.json()["access_token"]
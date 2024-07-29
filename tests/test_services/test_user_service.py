#tests/test_services/test_user_service.py
from fastapi import HTTPException
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient
from app.main import app
from app.database import Database
from app.models.user_model import User
from app.services.user_service import UserService
from app.dependencies import get_email_service, get_settings
import uuid

settings = get_settings()

@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
async def db_session():
    async with Database.get_session_factory()() as session:
        yield session

@pytest.fixture
async def email_service():
    return get_email_service()

@pytest.fixture
async def user(db_session: AsyncSession, email_service):
    user_data = {
        "email": "testuser@example.com",
        "password": "TestPassword123!"
    }
    user = await UserService.create(db_session, user_data, email_service)
    await db_session.commit()
    return user

@pytest.fixture
async def verified_user(db_session: AsyncSession, email_service):
    user_data = {
        "email": "verifieduser@example.com",
        "password": "VerifiedPassword123!"
    }
    user = await UserService.create(db_session, user_data, email_service)
    user.email_verified = True
    await db_session.commit()
    return user

@pytest.fixture
async def locked_user(db_session: AsyncSession, email_service):
    user_data = {
        "email": "lockeduser@example.com",
        "password": "LockedPassword123!"
    }
    user = await UserService.create(db_session, user_data, email_service)
    user.is_locked = True
    await db_session.commit()
    return user

@pytest.mark.asyncio
async def test_create_user_with_valid_data(db_session, email_service):
    user_data = {
        "email": f"valid_user_{uuid.uuid4()}@example.com",  # Generate a unique email
        "password": "ValidPassword123!"
    }
    user = await UserService.create(db_session, user_data, email_service)
    await db_session.commit()
    assert user is not None
    assert user.email == user_data["email"]

@pytest.mark.asyncio
async def test_create_user_with_invalid_data(db_session, email_service):
    user_data = {
        "nickname": "",  # Invalid nickname
        "email": "invalidemail",  # Invalid email
        "password": "short"  # Invalid password
    }
    with pytest.raises(HTTPException) as exc_info:
        await UserService.create(db_session, user_data, email_service)
    assert exc_info.value.status_code == 400
    assert "value is not a valid email address" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_get_by_id_user_exists(db_session, user):
    retrieved_user = await UserService.get_by_id(db_session, user.id)
    assert retrieved_user.id == user.id

@pytest.mark.asyncio
async def test_get_by_id_user_does_not_exist(db_session):
    non_existent_user_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
    retrieved_user = await UserService.get_by_id(db_session, non_existent_user_id)
    assert retrieved_user is None

@pytest.mark.asyncio
async def test_get_by_nickname_user_exists(db_session, user):
    retrieved_user = await UserService.get_by_nickname(db_session, user.nickname)
    assert retrieved_user.nickname == user.nickname

@pytest.mark.asyncio
async def test_get_by_nickname_user_does_not_exist(db_session):
    retrieved_user = await UserService.get_by_nickname(db_session, "non_existent_nickname")
    assert retrieved_user is None

@pytest.mark.asyncio
async def test_get_by_email_user_exists(db_session, user):
    retrieved_user = await UserService.get_by_email(db_session, user.email)
    assert retrieved_user.email == user.email

@pytest.mark.asyncio
async def test_get_by_email_user_does_not_exist(db_session):
    retrieved_user = await UserService.get_by_email(db_session, "non_existent_email@example.com")
    assert retrieved_user is None

@pytest.mark.asyncio
async def test_update_user_valid_data(db_session, user):
    new_email = "updated_email@example.com"
    updated_user = await UserService.update(db_session, user.id, {"email": new_email})
    await db_session.commit()
    assert updated_user is not None
    assert updated_user.email == new_email

@pytest.mark.asyncio
async def test_update_user_invalid_data(db_session, user):
    with pytest.raises(ValueError):
        await UserService.update(db_session, user.id, {"email": "invalidemail"})

@pytest.mark.asyncio
async def test_delete_user_exists(db_session, user):
    deletion_success = await UserService.delete(db_session, user.id)
    await db_session.commit()
    assert deletion_success is True

@pytest.mark.asyncio
async def test_delete_user_does_not_exist(db_session):
    non_existent_user_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
    deletion_success = await UserService.delete(db_session, non_existent_user_id)
    await db_session.commit()
    assert deletion_success is False

@pytest.mark.asyncio
async def test_list_users_with_pagination(db_session, user, email_service):
    for i in range(20):
        await UserService.create(db_session, {"email": f"user{i}@example.com", "password": "password123"}, email_service)
    users_page_1 = await UserService.list_users(db_session, skip=0, limit=10)
    users_page_2 = await UserService.list_users(db_session, skip=10, limit=10)
    assert len(users_page_1) == 10
    assert len(users_page_2) == 10
    assert users_page_1[0].id != users_page_2[0].id

@pytest.mark.asyncio
async def test_register_user_with_valid_data(db_session, email_service):
    user_data = {
        "email": f"register_valid_user_{uuid.uuid4()}@example.com",  # Generate a unique email
        "password": "RegisterValid123!"
    }
    user = await UserService.register_user(db_session, user_data, email_service)
    await db_session.commit()
    assert user is not None
    assert user.email == user_data["email"]

@pytest.mark.asyncio
async def test_register_user_with_invalid_data(db_session, email_service):
    user_data = {
        "email": "registerinvalidemail",  # Invalid email
        "password": "short"  # Invalid password
    }
    with pytest.raises(HTTPException) as exc_info:
        await UserService.register_user(db_session, user_data, email_service)
    assert exc_info.value.status_code == 400
    assert "value is not a valid email address" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_login_user_successful(db_session, verified_user):
    user_data = {
        "email": verified_user.email,
        "password": "VerifiedPassword123!"
    }
    logged_in_user = await UserService.login_user(db_session, user_data["email"], user_data["password"])
    assert logged_in_user is not None

@pytest.mark.asyncio
async def test_login_user_incorrect_email(db_session):
    user = await UserService.login_user(db_session, "nonexistentuser@noway.com", "Password123!")
    assert user is None

@pytest.mark.asyncio
async def test_login_user_incorrect_password(db_session, user):
    user = await UserService.login_user(db_session, user.email, "IncorrectPassword!")
    assert user is None

@pytest.mark.asyncio
async def test_account_lock_after_failed_logins(db_session, verified_user):
    max_login_attempts = settings.max_login_attempts
    for _ in range(max_login_attempts):
        await UserService.login_user(db_session, verified_user.email, "wrongpassword")
    
    is_locked = await UserService.is_account_locked(db_session, verified_user.email)
    assert is_locked, "The account should be locked after the maximum number of failed login attempts."

@pytest.mark.asyncio
async def test_reset_password(db_session, user):
    new_password = "NewPassword123!"
    reset_success = await UserService.reset_password(db_session, user.id, new_password)
    await db_session.commit()
    assert reset_success is True

@pytest.mark.asyncio
async def test_verify_email_with_token(db_session, user):
    token = "valid_token_example"
    user.verification_token = token
    await db_session.commit()
    result = await UserService.verify_email_with_token(db_session, user.id, token)
    assert result is True

@pytest.mark.asyncio
async def test_unlock_user_account(db_session, locked_user):
    unlocked = await UserService.unlock_user_account(db_session, locked_user.id)
    await db_session.commit()
    assert unlocked, "The account should be unlocked"
    refreshed_user = await UserService.get_by_id(db_session, locked_user.id)
    assert not refreshed_user.is_locked, "The user should no longer be locked"

@pytest.mark.asyncio
async def test_create_user_access_denied(async_client, user_token):
    headers = {"Authorization": f"Bearer {user_token}"}
    user_data = {"nickname": "newuser", "email": "test@example.com", "password": "StrongPassword123!"}
    response = await async_client.post("/users/", json=user_data, headers=headers)
    assert response.status_code == 403
    assert "Operation not permitted" in response.json().get("detail", "")
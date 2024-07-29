from builtins import repr
from datetime import datetime, timezone
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user_model import User, UserRole
import uuid

@pytest.mark.asyncio
async def test_user_role(db_session: AsyncSession, user: User, admin_user: User, manager_user: User):
    assert user.role == UserRole.AUTHENTICATED, "Default role should be USER"
    assert admin_user.role == UserRole.ADMIN, "Admin role should be correctly assigned"
    assert manager_user.role == UserRole.MANAGER, "Pro role should be correctly assigned"

@pytest.mark.asyncio
async def test_has_role(user: User, admin_user: User, manager_user: User):
    assert user.has_role(UserRole.AUTHENTICATED), "User should have USER role"
    assert not user.has_role(UserRole.ADMIN), "User should not have ADMIN role"
    assert admin_user.has_role(UserRole.ADMIN), "Admin user should have ADMIN role"
    assert manager_user.has_role(UserRole.MANAGER), "Pro user should have PRO role"

@pytest.mark.asyncio
async def test_user_repr(user: User):
    assert repr(user) == f"<User {user.nickname}, Role: {user.role.name}>", "__repr__ should include nickname and role"

@pytest.mark.asyncio
async def test_failed_login_attempts_increment(db_session: AsyncSession, user: User):
    initial_attempts = user.failed_login_attempts
    user.failed_login_attempts += 1
    await db_session.commit()
    await db_session.refresh(user)
    assert user.failed_login_attempts == initial_attempts + 1, "Failed login attempts should increment"

@pytest.mark.asyncio
async def test_last_login_update(db_session: AsyncSession, user: User):
    new_last_login = datetime.now(timezone.utc)
    user.last_login_at = new_last_login
    await db_session.commit()
    await db_session.refresh(user)
    assert user.last_login_at == new_last_login, "Last login timestamp should update correctly"

@pytest.mark.asyncio
async def test_account_lock_and_unlock(db_session: AsyncSession, user: User):
    assert not user.is_locked, "Account should initially be unlocked"
    user.lock_account()
    await db_session.commit()
    await db_session.refresh(user)
    assert user.is_locked, "Account should be locked after calling lock_account()"
    user.unlock_account()
    await db_session.commit()
    await db_session.refresh(user)
    assert not user.is_locked, "Account should be unlocked after calling unlock_account()"

@pytest.mark.asyncio
async def test_email_verification(db_session: AsyncSession, user: User):
    assert not user.email_verified, "Email should initially be unverified"
    user.verify_email()
    await db_session.commit()
    await db_session.refresh(user)
    assert user.email_verified, "Email should be verified after calling verify_email()"

@pytest.mark.asyncio
async def test_user_profile_pic_url_update(db_session: AsyncSession, user: User):
    profile_pic_url = "http://myprofile/picture.png"
    user.profile_picture_url = profile_pic_url
    await db_session.commit()
    await db_session.refresh(user)
    assert user.profile_picture_url == profile_pic_url, "The profile pic did not update"

@pytest.mark.asyncio
async def test_user_linkedin_url_update(db_session: AsyncSession, user: User):
    profile_linkedin_url = "http://www.linkedin.com/profile"
    user.linkedin_profile_url = profile_linkedin_url
    await db_session.commit()
    await db_session.refresh(user)
    assert user.linkedin_profile_url == profile_linkedin_url, "The LinkedIn profile URL did not update"

@pytest.mark.asyncio
async def test_user_github_url_update(db_session: AsyncSession, user: User):
    profile_github_url = "http://www.github.com/profile"
    user.github_profile_url = profile_github_url
    await db_session.commit()
    await db_session.refresh(user)
    assert user.github_profile_url == profile_github_url, "The GitHub profile URL did not update"

@pytest.mark.asyncio
async def test_default_role_assignment(db_session: AsyncSession):
    user = User(nickname="noob", email="newuser@example.com", hashed_password="hashed_password")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    assert user.role == UserRole.ANONYMOUS, "Default role should be 'anonymous' if not specified"

@pytest.mark.asyncio
async def test_update_user_role(db_session: AsyncSession, user: User):
    user.role = UserRole.ADMIN
    await db_session.commit()
    await db_session.refresh(user)
    assert user.role == UserRole.ADMIN, "Role update should persist correctly in the database"

@pytest.mark.asyncio
async def test_is_professional_flag(db_session: AsyncSession, user: User):
    assert not user.is_professional, "User should not be professional by default"
    user.is_professional = True
    await db_session.commit()
    await db_session.refresh(user)
    assert user.is_professional, "User should be marked as professional"

@pytest.mark.asyncio
async def test_professional_status_updated_at(db_session: AsyncSession, user: User):
    assert user.professional_status_updated_at is None, "Professional status update time should be None initially"
    update_time = datetime.now(timezone.utc)
    user.professional_status_updated_at = update_time
    await db_session.commit()
    await db_session.refresh(user)
    assert user.professional_status_updated_at == update_time, "Professional status update time should be set correctly"

@pytest.mark.asyncio
async def test_user_bio_update(db_session: AsyncSession, user: User):
    new_bio = "This is a new bio for the user"
    user.bio = new_bio
    await db_session.commit()
    await db_session.refresh(user)
    assert user.bio == new_bio, "User bio should update correctly"

@pytest.mark.asyncio
async def test_created_and_updated_at(db_session: AsyncSession):
    user = User(nickname="timeuser", email="timeuser@example.com", hashed_password="hashed_password")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    assert user.created_at is not None, "created_at should be set automatically"
    assert user.updated_at is not None, "updated_at should be set automatically"
    assert user.created_at == user.updated_at, "created_at and updated_at should be the same on creation"

    # Update the user
    original_updated_at = user.updated_at
    user.nickname = "newtimeuser"
    await db_session.commit()
    await db_session.refresh(user)
    assert user.updated_at > original_updated_at, "updated_at should change after an update"
    assert user.created_at < user.updated_at, "created_at should be earlier than updated_at after an update"
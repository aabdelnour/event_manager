from typing import Optional, Dict, List
from sqlalchemy import select, update, func
from sqlalchemy.exc import SQLAlchemyError
from app.dependencies import get_settings
from app.models.user_model import User, UserRole
from app.schemas.user_schemas import UserCreate, UserUpdate
from app.utils.security import hash_password, verify_password, generate_verification_token
from app.utils.nickname_gen import generate_nickname
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import traceback

logger = logging.getLogger(__name__)
from app.services.email_service import EmailService
from app.database import get_session
from fastapi import HTTPException

class UserService:
    @classmethod
    async def create(cls, session: AsyncSession, user_data: Dict[str, str], email_service: EmailService) -> Optional[User]:
        try:
            validated_data = UserCreate(**user_data).model_dump()
            existing_user = await cls.get_by_email(session, validated_data['email'])
            if existing_user:
                logger.error("User with given email already exists.")
                raise HTTPException(status_code=400, detail="User with given email already exists.")
            
            validated_data['hashed_password'] = hash_password(validated_data.pop('password'))
            new_user = User(**validated_data)
            new_user.verification_token = generate_verification_token()
            new_nickname = generate_nickname()
            while await cls.get_by_nickname(session, new_nickname):
                new_nickname = generate_nickname()
            new_user.nickname = new_nickname
            session.add(new_user)
            await session.commit()
            try:
                await email_service.send_verification_email(new_user)
            except Exception as e:
                logger.error(f"Failed to send verification email: {e}")
                # Handle the email sending failure gracefully
                # You can choose to either raise an exception or continue with user creation
                # raise HTTPException(status_code=500, detail="Failed to send verification email")
            return new_user
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"Error during user creation: {e}")
            logger.error(traceback.format_exc())
            await session.rollback()
            raise HTTPException(status_code=500, detail="Internal server error")
        
    @classmethod
    async def get_by_email(cls, session: AsyncSession, email: str) -> Optional[User]:
        query = select(User).where(User.email == email)
        result = await session.execute(query)
        return result.scalars().first()

    @classmethod
    async def get_by_id(cls, session: AsyncSession, user_id: UUID) -> Optional[User]:
        query = select(User).where(User.id == user_id)
        result = await session.execute(query)
        return result.scalars().first()

    @classmethod
    async def get_by_nickname(cls, session: AsyncSession, nickname: str) -> Optional[User]:
        query = select(User).where(User.nickname == nickname)
        result = await session.execute(query)
        return result.scalars().first()

    @classmethod
    async def update(cls, session: AsyncSession, user_id: UUID, update_data: Dict[str, str]) -> Optional[User]:
        try:
            validated_data = UserUpdate(**update_data).dict(exclude_unset=True)
            if 'password' in validated_data:
                validated_data['hashed_password'] = hash_password(validated_data.pop('password'))
            await session.execute(update(User).where(User.id == user_id).values(**validated_data))
            await session.commit()
            return await cls.get_by_id(session, user_id)
        except Exception as e:
            logging.error(f"Error during user update: {e}")
            await session.rollback()
            return None

    @classmethod
    async def delete(cls, session: AsyncSession, user_id: UUID) -> bool:
        try:
            user = await cls.get_by_id(session, user_id)
            if user:
                await session.delete(user)
                await session.commit()
                return True
            else:
                return False
        except Exception as e:
            logging.error(f"Error during user deletion: {e}")
            await session.rollback()
            return False

    @classmethod
    async def list_users(cls, session: AsyncSession, skip: int = 0, limit: int = 10) -> List[User]:
        query = select(User).offset(skip).limit(limit)
        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def register_user(cls, session: AsyncSession, user_data: Dict[str, str], email_service: EmailService) -> Optional[User]:
        return await cls.create(session, user_data, email_service)
    
    @classmethod
    async def login_user(cls, session: AsyncSession, email: str, password: str) -> Optional[User]:
        user = await cls.get_by_email(session, email)
        if user and verify_password(password, user.hashed_password):
            user.failed_login_attempts = 0
            session.add(user)
            await session.commit()
            return user
        else:
            if user:
                user.failed_login_attempts += 1
                session.add(user)
                await session.commit()
            return None

    @classmethod
    async def verify_email_with_token(cls, session: AsyncSession, user_id: UUID, token: str) -> bool:
        user = await cls.get_by_id(session, user_id)
        if user and user.verification_token == token:
            user.email_verified = True
            user.verification_token = None  # Clear the token once used
            session.add(user)
            await session.commit()
            return True
        return False

    @classmethod
    async def is_account_locked(cls, session: AsyncSession, email: str) -> bool:
        user = await cls.get_by_email(session, email)
        return user.is_locked if user else False

    @classmethod
    async def count(cls, session: AsyncSession) -> int:
        result = await session.execute(select(func.count()).select_from(User))
        return result.scalar_one()
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user_model import User
from app.utils.security import verify_password

async def authenticate_user(db: AsyncSession, username: str, password: str):
    async with db() as session:
        result = await session.execute(select(User).where(User.email == username))
        user = result.scalars().first()
        if user and verify_password(password, user.hashed_password):
            return user
        return None

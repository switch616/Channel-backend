from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext
from datetime import datetime, timezone

from app.models.mysql.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.utils.security import verify_password, hash_password

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# 根据邮箱查询用户
async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()


# 根据用户ID查询用户
async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()


# 分页获取所有用户
async def get_all_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()


# 创建新用户
async def create_user(db: AsyncSession, user: UserCreate) -> User:
    # 对密码进行加密处理
    hashed_password = pwd_context.hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        password=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name,
        full_name=user.full_name,
        bio=user.bio,
        phone_number=user.phone_number,
        profile_picture=user.profile_picture,
        address=user.address,
        city=user.city,
        state=user.state,
        country=user.country,
        postal_code=user.postal_code,
        password_updated_at=datetime.now(timezone.utc),
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


# 更新用户信息（基于UserUpdate Pydantic模型）
async def update_user(db: AsyncSession, db_user: User, user_update: UserUpdate) -> User:
    # 只更新被显式传入的字段
    update_data = user_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)
    await db.commit()
    await db.refresh(db_user)
    return db_user


# 删除用户
async def delete_user(db: AsyncSession, user_id: int) -> bool:
    result = await db.execute(select(User).where(User.id == user_id))
    db_user = result.scalars().first()
    if db_user:
        await db.delete(db_user)  # 异步删除
        await db.commit()
        return True
    return False


# 更新用户头像路径
async def update_user_profile_picture(db: AsyncSession, user_id: int, path: str) -> bool:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        return False
    user.profile_picture = path
    await db.commit()
    return True


# 更新用户资料（如昵称、简介、性别等）
async def update_user_profile(db: AsyncSession, user_id: int, update_data: dict) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        return None
    for key, value in update_data.items():
        setattr(user, key, value)
    await db.commit()
    await db.refresh(user)
    return user


def check_password(db_user, password: str) -> bool:
    return verify_password(password, db_user.password)

def update_password(db, db_user, new_password: str):
    db_user.password = hash_password(new_password)
    db.commit()
    db.refresh(db_user)
    return db_user

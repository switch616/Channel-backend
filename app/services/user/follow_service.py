from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.user.follow import toggle_follow, is_following, get_fans_count, get_following_count, get_following_list, get_fans_list

async def toggle_follow_service(db: AsyncSession, user_id: int, followed_user_id: int) -> bool:
    return await toggle_follow(db, user_id, followed_user_id)

async def is_following_service(db: AsyncSession, user_id: int, followed_user_id: int) -> bool:
    return await is_following(db, user_id, followed_user_id)

async def get_fans_count_service(db: AsyncSession, user_id: int) -> int:
    return await get_fans_count(db, user_id)

async def get_following_count_service(db: AsyncSession, user_id: int) -> int:
    return await get_following_count(db, user_id)

async def get_following_list_service(db, user_id, page, size, search=None, order='desc', current_user_id=None):
    return await get_following_list(db, user_id, page, size, search, order, current_user_id)

async def get_fans_list_service(db, user_id, page, size, search=None, current_user_id=None):
    return await get_fans_list(db, user_id, page, size, search, current_user_id) 
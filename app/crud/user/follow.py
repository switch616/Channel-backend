from sqlalchemy import select, func, desc, asc, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.mysql.follow import Follow
from app.models.mysql.user import User

async def toggle_follow(db: AsyncSession, user_id: int, followed_user_id: int) -> bool:
    existing = await db.scalar(
        select(Follow).where(Follow.user_id == user_id, Follow.followed_user_id == followed_user_id)
    )
    if existing:
        await db.delete(existing)
        await db.commit()
        return False
    else:
        follow = Follow(user_id=user_id, followed_user_id=followed_user_id)
        db.add(follow)
        await db.commit()
        return True

async def is_following(db: AsyncSession, user_id: int, followed_user_id: int) -> bool:
    result = await db.scalar(
        select(Follow).where(Follow.user_id == user_id, Follow.followed_user_id == followed_user_id)
    )
    return result is not None

async def get_fans_count(db: AsyncSession, user_id: int) -> int:
    result = await db.scalar(
        select(func.count(Follow.id)).where(Follow.followed_user_id == user_id)
    )
    return result or 0

async def get_following_count(db: AsyncSession, user_id: int) -> int:
    result = await db.scalar(
        select(func.count(Follow.id)).where(Follow.user_id == user_id)
    )
    return result or 0

async def get_following_list(db: AsyncSession, user_id: int, page: int, size: int, search: str = None, order: str = 'desc', current_user_id: int = None):
    stmt = select(Follow, User).join(User, Follow.followed_user_id == User.id).where(Follow.user_id == user_id)
    if search:
        stmt = stmt.where(or_(User.username.ilike(f'%{search}%'), User.unique_id.ilike(f'%{search}%')))
    if order == 'asc':
        stmt = stmt.order_by(asc(Follow.created_at))
    else:
        stmt = stmt.order_by(desc(Follow.created_at))
    stmt = stmt.offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    
    items = []
    for f, u in result.all():
        # 检查当前用户是否关注了列表中的用户
        is_followed = True  # 关注列表中的用户都是已关注的
        is_mutual = False   # 是否互相关注
        
        if current_user_id and current_user_id != u.id:
            # 检查对方是否也关注了当前用户（互相关注）
            is_mutual = await is_following(db, u.id, current_user_id)
        
        items.append(dict(
            id=u.id,
            username=u.username,
            unique_id=u.unique_id,
            profile_picture=u.profile_picture,
            bio=u.bio,  # 添加bio字段
            created_at=f.created_at.strftime('%Y-%m-%d %H:%M:%S') if f.created_at else '',
            is_followed=is_followed,
            is_mutual=is_mutual
        ))
    
    total = await db.scalar(select(func.count()).select_from(Follow).where(Follow.user_id == user_id))
    return {"total": total, "items": items}

async def get_fans_list(db: AsyncSession, user_id: int, page: int, size: int, search: str = None, current_user_id: int = None):
    stmt = select(Follow, User).join(User, Follow.user_id == User.id).where(Follow.followed_user_id == user_id)
    if search:
        stmt = stmt.where(or_(User.username.ilike(f'%{search}%'), User.unique_id.ilike(f'%{search}%')))
    stmt = stmt.order_by(desc(Follow.created_at)).offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    
    items = []
    for f, u in result.all():
        # 检查当前用户是否关注了粉丝列表中的用户
        is_followed = False
        is_mutual = False
        
        if current_user_id and current_user_id != u.id:
            is_followed = await is_following(db, current_user_id, u.id)
            # 如果当前用户关注了该粉丝，则为互相关注
            is_mutual = is_followed
        
        items.append(dict(
            id=u.id,
            username=u.username,
            unique_id=u.unique_id,
            profile_picture=u.profile_picture,
            bio=u.bio,  # 添加bio字段
            created_at=f.created_at.strftime('%Y-%m-%d %H:%M:%S') if f.created_at else '',
            is_followed=is_followed,
            is_mutual=is_mutual
        ))
    
    total = await db.scalar(select(func.count()).select_from(Follow).where(Follow.followed_user_id == user_id))
    return {"total": total, "items": items} 
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mysql.collection import Collection
from app.models.mysql.video import Video


async def toggle_video_collection(db: AsyncSession, video_id: int, user_id: int) -> bool:
    """切换视频收藏状态"""
    # 检查是否已收藏
    existing = await db.scalar(
        select(Collection).where(Collection.video_id == video_id, Collection.user_id == user_id)
    )
    
    if existing:
        # 取消收藏
        await db.delete(existing)
        await db.commit()
        
        # 更新视频收藏数
        await update_video_collect_count(db, video_id)
        return False
    else:
        # 添加收藏
        collection = Collection(video_id=video_id, user_id=user_id)
        db.add(collection)
        await db.commit()
        
        # 更新视频收藏数
        await update_video_collect_count(db, video_id)
        return True


async def update_video_collect_count(db: AsyncSession, video_id: int) -> None:
    """更新视频收藏数"""
    collect_count = await db.scalar(
        select(func.count(Collection.id)).where(Collection.video_id == video_id)
    )
    
    video = await db.scalar(select(Video).where(Video.id == video_id))
    if video:
        video.collect_count = collect_count or 0
        await db.commit()


async def get_user_collection_status(db: AsyncSession, video_id: int, user_id: int) -> bool:
    """获取用户对视频的收藏状态"""
    result = await db.scalar(
        select(Collection).where(Collection.video_id == video_id, Collection.user_id == user_id)
    )
    return result is not None


async def get_video_collect_count(db: AsyncSession, video_id: int) -> int:
    """获取视频收藏数"""
    result = await db.scalar(
        select(func.count(Collection.id)).where(Collection.video_id == video_id)
    )
    return result or 0 
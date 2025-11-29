from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mysql.like import Like
from app.models.mysql.video import Video


async def toggle_video_like(db: AsyncSession, video_id: int, user_id: int) -> bool:
    """切换视频点赞状态"""
    # 检查是否已点赞
    existing = await db.scalar(
        select(Like).where(Like.video_id == video_id, Like.user_id == user_id)
    )
    
    if existing:
        # 取消点赞
        await db.delete(existing)
        await db.commit()
        
        # 更新视频点赞数
        await update_video_like_count(db, video_id)
        return False
    else:
        # 添加点赞
        like = Like(video_id=video_id, user_id=user_id)
        db.add(like)
        await db.commit()
        
        # 更新视频点赞数
        await update_video_like_count(db, video_id)
        return True


async def update_video_like_count(db: AsyncSession, video_id: int) -> None:
    """更新视频点赞数"""
    like_count = await db.scalar(
        select(func.count(Like.id)).where(Like.video_id == video_id)
    )
    
    video = await db.scalar(select(Video).where(Video.id == video_id))
    if video:
        video.like_count = like_count or 0
        await db.commit()


async def get_user_like_status(db: AsyncSession, video_id: int, user_id: int) -> bool:
    """获取用户对视频的点赞状态"""
    result = await db.scalar(
        select(Like).where(Like.video_id == video_id, Like.user_id == user_id)
    )
    return result is not None


async def get_video_like_count(db: AsyncSession, video_id: int) -> int:
    """获取视频点赞数"""
    result = await db.scalar(
        select(func.count(Like.id)).where(Like.video_id == video_id)
    )
    return result or 0 
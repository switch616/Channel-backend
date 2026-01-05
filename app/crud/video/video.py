from typing import Optional, List, Tuple
from sqlalchemy import desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.models.mysql.video import Video
from app.schemas.video import VideoCreate, VideoUpdate


# 统计某用户发布的视频数量（排除已删除）
async def count_user_videos(db: AsyncSession, user_id: int) -> int:
    result = await db.execute(
        select(func.count()).select_from(Video).where(
            Video.uploader_id == user_id,
            Video.is_deleted == False
        )
    )
    return result.scalar_one()


# 根据视频ID获取视频详情
async def get_video_by_id(db: AsyncSession, video_id: int) -> Optional[Video]:
    result = await db.execute(
        select(Video).where(
            Video.id == video_id,
            Video.is_deleted == False
        )
    )
    return result.scalars().first()



# 获取所有视频（分页，主要用于后台管理）
async def get_all_videos(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Video]:
    result = await db.execute(select(Video).offset(skip).limit(limit))
    return result.scalars().all()


# 创建视频记录
async def create_video(db: AsyncSession, video_data: VideoCreate, uploader_id: int) -> Video:
    db_video = Video(**video_data.dict(), uploader_id=uploader_id)
    db.add(db_video)
    await db.commit()
    await db.refresh(db_video)
    return db_video


# 更新视频信息（仅更新传入字段）
async def update_video(db: AsyncSession, db_video: Video, update_data: VideoUpdate) -> Video:
    data = update_data.dict(exclude_unset=True)
    for key, value in data.items():
        setattr(db_video, key, value)
    await db.commit()
    await db.refresh(db_video)
    return db_video


# 删除视频（硬删除，可改为软删除）
async def delete_video(db: AsyncSession, video_id: int) -> bool:
    result = await db.execute(select(Video).where(Video.id == video_id))
    db_video = result.scalars().first()
    if db_video:
        await db.delete(db_video)
        await db.commit()
        return True
    return False


# 获取当前用户上传的视频（带分页和上传者信息）
async def get_my_videos(
    db: AsyncSession,
    user_id: int,
    skip: int,
    limit: int,
) -> Tuple[int, List[Video]]:

    total_stmt = select(func.count(Video.id)).where(
        Video.uploader_id == user_id,
        Video.is_deleted == False
    )
    total = await db.scalar(total_stmt)

    stmt = (
        select(Video)
        .options(joinedload(Video.uploader))
        .where(
            Video.uploader_id == user_id,
            Video.is_deleted == False
        )
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    video_list = result.scalars().unique().all()

    return total, video_list



# 获取推荐视频列表（公开 + 未删除 + 排序，含分页）
async def get_recommend_video_list(db: AsyncSession, skip: int, limit: int) -> Tuple[int, List[Video]]:
    # 查询符合条件的视频总数
    total_stmt = select(func.count(Video.id)).where(Video.is_public == True, Video.is_deleted == False)
    total = await db.scalar(total_stmt)

    # 按照浏览量和创建时间排序
    stmt = (
        select(Video)
        .options(joinedload(Video.uploader))
        .where(Video.is_public == True, Video.is_deleted == False)
        .order_by(desc(Video.view_count), desc(Video.created_at))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    video_list = result.scalars().unique().all()

    return total, video_list


# 获取最新视频列表（公开 + 未删除 + 创建时间倒序，含分页）
async def get_latest_video_list(db: AsyncSession, skip: int, limit: int):
    total_stmt = select(func.count(Video.id)).where(Video.is_public == True, Video.is_deleted == False)
    total = await db.scalar(total_stmt)
    stmt = (
        select(Video)
        .options(joinedload(Video.uploader))
        .where(Video.is_public == True, Video.is_deleted == False)
        .order_by(desc(Video.created_at))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    video_list = result.scalars().unique().all()
    return total, video_list


# 获取热门视频列表（公开 + 未删除 + 综合热度排序，含分页）
async def get_hot_video_list(db: AsyncSession, skip: int, limit: int):
    total_stmt = select(func.count(Video.id)).where(Video.is_public == True, Video.is_deleted == False)
    total = await db.scalar(total_stmt)
    # 热度算法：点赞数*2 + 评论数 + 播放量/10
    stmt = (
        select(Video)
        .options(joinedload(Video.uploader))
        .where(Video.is_public == True, Video.is_deleted == False)
        .order_by((Video.like_count * 2 + Video.comment_count + Video.view_count / 10).desc(), Video.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    video_list = result.scalars().unique().all()
    return total, video_list

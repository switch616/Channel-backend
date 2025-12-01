from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from app.models.mysql.watch_history import WatchHistory
from app.models.mysql.video import Video

from app.dependencies import get_db, get_current_user
from app.schemas.http.response import ResponseSchema
from app.services.analytics.analytics import (
    get_user_watch_history,
    get_popular_videos,
    get_video_analytics,
    log_video_view
)

router = APIRouter()


@router.get("/user/watch-history", response_model=ResponseSchema)
async def get_watch_history(
    limit: int = Query(50, le=100, description="获取数量"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取用户观看历史"""
    try:
        history = await get_user_watch_history(current_user.id, limit, db)
        return ResponseSchema.success(data=history)
    except Exception as e:
        return ResponseSchema.fail(msg=f"获取观看历史失败: {str(e)}")


@router.get("/user/watch-history-mysql", response_model=ResponseSchema)
async def get_watch_history_mysql(
    page: int = Query(1, ge=1),
    size: int = Query(20, le=50),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    offset = (page - 1) * size
    stmt = (
        select(WatchHistory)
        .where(WatchHistory.user_id == current_user.id)
        .order_by(WatchHistory.last_watch_at.desc())
        .offset(offset)
        .limit(size)
    )
    result = await db.execute(stmt)
    history_list = result.scalars().all()
    video_ids = [h.video_id for h in history_list]
    videos = {}
    if video_ids:
        v_result = await db.execute(
            select(Video)
            .options(joinedload(Video.uploader))  # 预加载 uploader，防止异步懒加载报错
            .where(Video.id.in_(video_ids))
        )
        for v in v_result.scalars().all():
            videos[v.id] = v
    items = []
    for h in history_list:
        v = videos.get(h.video_id)
        if v:
            items.append({
                'id': v.id,
                'title': v.title,
                'cover_image': v.cover_image,
                'file_path': v.file_path,
                'duration': v.duration,
                'uploader_id': v.uploader_id,
                'uploader_username': getattr(v.uploader, 'username', None) if hasattr(v, 'uploader') else None,
                'created_at': v.created_at,
                'like_count': v.like_count,
                'history_last_watch_at': h.last_watch_at,
                'history_watch_time': h.watch_time,
            })
    return ResponseSchema.success(data={'total': len(items), 'items': items})


@router.get("/videos/popular", response_model=ResponseSchema)
async def get_popular_videos_api(
    days: int = Query(7, ge=1, le=30, description="统计天数"),
    limit: int = Query(20, le=50, description="获取数量"),
    db: AsyncSession = Depends(get_db),
):
    """获取热门视频"""
    try:
        videos = await get_popular_videos(days, limit)
        return ResponseSchema.success(data=videos)
    except Exception as e:
        return ResponseSchema.fail(msg=f"获取热门视频失败: {str(e)}")


@router.get("/video/{video_id}/analytics", response_model=ResponseSchema)
async def get_video_analytics_api(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取视频分析数据"""
    try:
        analytics = await get_video_analytics(video_id)
        return ResponseSchema.success(data=analytics)
    except Exception as e:
        return ResponseSchema.fail(msg=f"获取视频分析失败: {str(e)}")


@router.post("/log_video_view", response_model=ResponseSchema)
async def log_video_view_api(
    data: dict = Body(...),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    记录视频观看历史（用户开始播放时调用）
    """
    video_id = data.get('video_id')
    if not video_id:
        return ResponseSchema.fail(msg="缺少 video_id")
    try:
        await log_video_view(
            user_id=current_user.id,
            video_id=video_id,
            watch_duration=data.get('watch_duration', 0),
            watch_progress=data.get('watch_progress', 0.0),
            device_info=data.get('device_info', {}),
            db=db
        )
        return ResponseSchema.success(msg="观看历史已记录")
    except Exception as e:
        return ResponseSchema.fail(msg=f"记录观看历史失败: {str(e)}")


@router.delete("/watch-history/{video_id}", response_model=ResponseSchema)
async def delete_watch_history(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """删除观看历史"""
    history = await db.scalar(select(WatchHistory).where(WatchHistory.video_id == video_id, WatchHistory.user_id == current_user.id))
    if not history:
        return ResponseSchema.fail(msg="未找到观看历史记录")
    await db.delete(history)
    await db.commit()
    return ResponseSchema.success(msg="已删除观看历史") 
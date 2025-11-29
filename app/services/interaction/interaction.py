from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.interaction.like import (
    toggle_video_like,
    get_user_like_status,
    get_video_like_count
)
from app.crud.interaction.collection import (
    toggle_video_collection,
    get_user_collection_status,
    get_video_collect_count
)
from app.services.analytics.analytics import log_user_behavior, update_video_analytics


async def toggle_video_like_service(
    db: AsyncSession,
    video_id: int,
    user_id: int
) -> dict:
    """切换视频点赞状态"""
    is_liked = await toggle_video_like(db, video_id, user_id)
    like_count = await get_video_like_count(db, video_id)
    
    # 记录用户行为到MongoDB（异步）
    try:
        await log_user_behavior(
            user_id=user_id,
            action="like" if is_liked else "unlike",
            target_type="video",
            target_id=video_id
        )
        
        # 更新视频分析数据
        await update_video_analytics(
            video_id=video_id,
            like_count=like_count
        )
    except Exception as e:
        # MongoDB操作失败不影响主流程
        print(f"MongoDB logging failed: {e}")
    
    return {
        "success": True,
        "message": "点赞成功" if is_liked else "取消点赞",
        "like_count": like_count,
        "is_liked": is_liked
    }


async def toggle_video_collection_service(
    db: AsyncSession,
    video_id: int,
    user_id: int
) -> dict:
    """切换视频收藏状态"""
    is_collected = await toggle_video_collection(db, video_id, user_id)
    collect_count = await get_video_collect_count(db, video_id)
    
    # 记录用户行为到MongoDB（异步）
    try:
        await log_user_behavior(
            user_id=user_id,
            action="collect" if is_collected else "uncollect",
            target_type="video",
            target_id=video_id
        )
        
        # 更新视频分析数据
        await update_video_analytics(
            video_id=video_id,
            collect_count=collect_count
        )
    except Exception as e:
        # MongoDB操作失败不影响主流程
        print(f"MongoDB logging failed: {e}")
    
    return {
        "success": True,
        "message": "收藏成功" if is_collected else "取消收藏",
        "collect_count": collect_count,
        "is_collected": is_collected
    }


async def get_video_interaction_status(
    db: AsyncSession,
    video_id: int,
    user_id: int
) -> dict:
    """获取视频交互状态（点赞、收藏）"""
    is_liked = await get_user_like_status(db, video_id, user_id)
    is_collected = await get_user_collection_status(db, video_id, user_id)
    like_count = await get_video_like_count(db, video_id)
    collect_count = await get_video_collect_count(db, video_id)
    
    return {
        "is_liked": is_liked,
        "is_collected": is_collected,
        "like_count": like_count,
        "collect_count": collect_count
    } 
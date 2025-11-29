from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from app.db.mongodb import get_mongo_db
from app.models.mongodb import UserBehaviorLog, VideoViewHistory, VideoAnalytics
from app.models.mysql.video import Video
from app.models.mysql.watch_history import WatchHistory
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy import update as sqlalchemy_update


async def log_user_behavior(
    user_id: int,
    action: str,
    target_type: str,
    target_id: int,
    metadata: Dict[str, Any] = None
):
    """记录用户行为日志"""
    db = get_mongo_db()
    behavior = UserBehaviorLog(
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        metadata=metadata or {}
    )
    
    await db[behavior.Config.collection].insert_one(behavior.dict())


async def log_video_view(
    user_id: int,
    video_id: int,
    watch_duration: int = 0,
    watch_progress: float = 0.0,
    device_info: Dict[str, str] = None,
    db: AsyncSession = None
):
    """记录视频观看历史，MongoDB+MySQL"""
    # MongoDB
    db_mongo = get_mongo_db()
    view = VideoViewHistory(
        user_id=user_id,
        video_id=video_id,
        watch_duration=watch_duration,
        watch_progress=watch_progress,
        device_info=device_info or {}
    )
    await db_mongo[view.Config.collection].insert_one(view.dict())
    # MySQL
    if db:
        # 查找是否已有记录
        result = await db.execute(select(WatchHistory).where(WatchHistory.user_id == user_id, WatchHistory.video_id == video_id))
        wh = result.scalars().first()
        now = datetime.utcnow()
        if wh:
            wh.watch_time = watch_duration
            wh.last_watch_at = now
        else:
            wh = WatchHistory(user_id=user_id, video_id=video_id, watch_time=watch_duration, last_watch_at=now)
            db.add(wh)
        await db.commit()


async def update_video_analytics(video_id: int, **updates):
    """更新视频分析数据"""
    db = get_mongo_db()
    collection = db[VideoAnalytics.Config.collection]
    
    # 使用upsert确保记录存在
    await collection.update_one(
        {"video_id": video_id},
        {"$set": {**updates, "updated_at": datetime.utcnow()}},
        upsert=True
    )


async def get_video_analytics(video_id: int) -> Optional[Dict[str, Any]]:
    """获取视频分析数据"""
    db = get_mongo_db()
    collection = db[VideoAnalytics.Config.collection]
    
    result = await collection.find_one({"video_id": video_id})
    return result


async def get_user_watch_history(user_id: int, limit: int = 50, db: AsyncSession = None) -> list:
    """
    获取用户观看历史，返回带视频详情的结构，适配前端 VideoGrid
    """
    db_mongo = get_mongo_db()
    collection = db_mongo[VideoViewHistory.Config.collection]
    cursor = collection.find({"user_id": user_id}).sort("timestamp", -1).limit(limit)
    history_list = await cursor.to_list(length=limit)
    video_ids = [h['video_id'] for h in history_list]
    # 查询视频详情
    video_map = {}
    if db and video_ids:
        result = await db.execute(select(Video).where(Video.id.in_(video_ids)))
        for v in result.scalars().all():
            video_map[v.id] = v
    # 组装前端需要的结构
    result_list = []
    for h in history_list:
        v = video_map.get(h['video_id'])
        if v:
            result_list.append({
                'id': v.id,
                'title': v.title,
                'cover_image': v.cover_image,
                'file_path': v.file_path,
                'duration': v.duration,
                'uploader_id': v.uploader_id,
                'uploader_username': getattr(v.uploader, 'username', None) if hasattr(v, 'uploader') else None,
                'created_at': v.created_at,
                'like_count': v.like_count,
                'history_timestamp': h.get('timestamp'),
                'history_watch_duration': h.get('watch_duration'),
                'history_watch_progress': h.get('watch_progress'),
            })
    return result_list


async def get_popular_videos(days: int = 7, limit: int = 20) -> List[Dict[str, Any]]:
    """获取热门视频（基于观看数据）"""
    db = get_mongo_db()
    collection = db[VideoViewHistory.Config.collection]
    
    # 计算时间范围
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # 聚合查询
    pipeline = [
        {"$match": {"timestamp": {"$gte": start_date}}},
        {"$group": {
            "_id": "$video_id",
            "view_count": {"$sum": 1},
            "total_watch_time": {"$sum": "$watch_duration"}
        }},
        {"$sort": {"view_count": -1}},
        {"$limit": limit}
    ]
    
    cursor = collection.aggregate(pipeline)
    return await cursor.to_list(length=limit) 
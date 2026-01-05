import os
import cv2
from uuid import uuid4
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import settings
from app.utils.file_validator import validate_video, validate_image
from app.storage.local import save_file_to_local
from app.schemas.video import VideoCreate, MyVideoListOut, RecommendVideoOut
from app.crud.video import create_video, get_my_videos, get_recommend_video_list, get_video_by_id, get_latest_video_list, get_hot_video_list,delete_video
from app.crud.user.user import get_user_by_id
from sqlalchemy import select, func
from app.models.mysql.like import Like
from app.models.mysql.collection import Collection
from app.models.mysql.comment import Comment
from app.services.interaction.interaction import get_video_interaction_status
from app.services.analytics.analytics import log_user_behavior, log_video_view, update_video_analytics
from app.models.mysql.video import Video
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.services.user.follow_service import is_following_service, get_fans_count_service
from app.schemas.http.response import BizCode

# 视频文件存储目录
VIDEO_DIR = os.path.join(settings.MEDIA_ROOT, "videos")
# 视频封面存储目录
COVER_DIR = os.path.join(settings.MEDIA_ROOT, "covers")


async def save_user_video(
        db: AsyncSession,
        video_file: UploadFile,
        cover_file: UploadFile,
        uploader_id: int,
        title: str,
        description: str,
) -> str:
    """
    校验上传的视频和封面文件，保存到本地并写入数据库。
    同时使用 OpenCV 获取视频时长（秒）。

    Args:
        db: 异步数据库会话
        video_file: 上传的视频文件
        cover_file: 上传的视频封面文件
        uploader_id: 上传用户ID
        title: 视频标题
        description: 视频描述

    Returns:
        str: 视频访问的完整URL路径
    """
    # 校验视频文件和封面图片合法性
    validate_video(video_file)
    validate_image(cover_file)

    # 生成视频文件名与路径
    ext_video = os.path.splitext(video_file.filename)[-1]
    video_filename = f"video_{uploader_id}_{uuid4().hex}{ext_video}"
    video_relative_path = os.path.join("media/videos", video_filename)
    video_full_path = os.path.join(settings.media_root_parent, video_relative_path)

    # 生成封面文件名与路径
    ext_cover = os.path.splitext(cover_file.filename)[-1]
    cover_filename = f"cover_{uploader_id}_{uuid4().hex}{ext_cover}"
    cover_relative_path = os.path.join("media/covers", cover_filename)
    cover_full_path = os.path.join(settings.media_root_parent, cover_relative_path)

    # 异步保存视频和封面到本地存储
    await save_file_to_local(video_file, video_full_path)
    await save_file_to_local(cover_file, cover_full_path)

    # 使用OpenCV打开视频文件，获取帧率和帧数，计算时长（秒）
    cap = cv2.VideoCapture(video_full_path)
    if not cap.isOpened():
        raise RuntimeError("无法打开视频文件")

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = int(frame_count / fps) if fps > 0 else 0
    cap.release()

    # 构造数据库插入数据结构
    video_data = VideoCreate(
        title=title,
        description=description,
        file_path=video_relative_path,
        cover_image=cover_relative_path,
        duration=duration,
    )
    # 创建视频记录
    await create_video(db, video_data, uploader_id)

    # 返回视频URL路径
    return f"{settings.MEDIA_URL.rstrip('/')}/{video_relative_path}"


async def get_my_video_list(db: AsyncSession, user_id: int, page: int, size: int = 20):
    """
    分页查询用户自己上传的视频列表，包含分页总数和视频详情列表。

    Args:
        db: 异步数据库会话
        user_id: 用户ID
        page: 当前页码，从1开始
        size: 每页数量，默认20

    Returns:
        dict: 包含总数total和视频列表items
    """
    skip = (page - 1) * size
    total, video_list = await get_my_videos(db=db, user_id=user_id, skip=skip, limit=size)

    # 组装返回列表，映射数据库模型到响应模型
    items = [
        MyVideoListOut(
            id=v.id,
            title=v.title,
            cover_image=v.cover_image,
            file_path=v.file_path,
            created_at=v.created_at,
            duration=v.duration,
            uploader_id=v.uploader.id,
            uploader_username=v.uploader.username,
            uploader_unique_id=v.uploader.unique_id,
            like_count=v.like_count,
        ) for v in video_list
    ]

    return {"total": total, "items": items}


async def get_recommended_videos(db: AsyncSession, page: int, size: int = 20):
    """
    分页获取推荐视频列表，包含视频总数和详情列表。
    推荐视频基于公开且未删除的视频，按播放量和创建时间排序。

    Args:
        db: 异步数据库会话
        page: 当前页码，从1开始
        size: 每页数量，默认20

    Returns:
        dict: 包含总数total和视频列表items
    """
    skip = (page - 1) * size
    total, video_list = await get_recommend_video_list(db=db, skip=skip, limit=size)

    # 组装推荐视频响应列表
    items = [
        RecommendVideoOut(
            id=v.id,
            title=v.title,
            cover_image=v.cover_image,
            file_path=v.file_path,
            created_at=v.created_at,
            duration=v.duration,
            uploader_id=v.uploader.id,
            uploader_username=v.uploader.username,
            uploader_unique_id=v.uploader.unique_id,
            like_count=v.like_count,
        )
        for v in video_list
    ]

    return {"total": total, "items": items}


async def get_video_detail(db: AsyncSession, video_id: int, current_user_id: int | None = None):
    """
    获取视频详情，包含视频基本信息、作者信息、评论数、点赞/收藏数、当前用户是否点赞/收藏。
    """
    # 1. 获取视频基本信息
    video = await get_video_by_id(db, video_id)
    if not video:
        return None

    # 2. 获取作者信息
    uploader = await get_user_by_id(db, video.uploader_id)
    if not uploader:
        uploader_info = None
    else:
        fans_count = await get_fans_count_service(db, uploader.id)
        is_followed = False
        is_follower = False
        is_mutual = False
        
        if current_user_id and uploader.id != current_user_id:
            # 检查当前用户是否关注了上传者
            is_followed = await is_following_service(db, current_user_id, uploader.id)
            # 检查上传者是否关注了当前用户
            is_follower = await is_following_service(db, uploader.id, current_user_id)
            # 检查是否互相关注
            is_mutual = is_followed and is_follower
            
        uploader_info = {
            "id": uploader.id,
            "username": uploader.username,
            "profile_picture": uploader.profile_picture or "/media/avatars/default.png",
            "fans_count": fans_count,
            "is_followed": is_followed,
            "is_mutual": is_mutual,
            "is_follower": is_follower
        }

    # 3. 评论数
    comment_count = await db.scalar(select(func.count(Comment.id)).where(Comment.video_id == video_id))
    
    # 4. 获取点赞/收藏状态和数量
    is_liked = False
    is_collected = False
    like_count = video.like_count
    collect_count = video.collect_count
    
    if current_user_id:
        try:
            interaction_status = await get_video_interaction_status(db, video_id, current_user_id)
            is_liked = interaction_status["is_liked"]
            is_collected = interaction_status["is_collected"]
            like_count = interaction_status["like_count"]
            collect_count = interaction_status["collect_count"]
        except Exception:
            # 如果获取交互状态失败，使用默认值
            pass

    # 5. 记录用户行为到MongoDB（异步，不阻塞响应）
    if current_user_id:
        try:
            # 记录视频查看行为
            await log_user_behavior(
                user_id=current_user_id,
                action="view",
                target_type="video",
                target_id=video_id,
                metadata={"title": video.title}
            )
            
            # 更新视频观看次数
            await update_video_analytics(
                video_id=video_id,
                view_count=video.view_count + 1
            )
        except Exception as e:
            # MongoDB操作失败不影响主流程
            print(f"MongoDB logging failed: {e}")

    # 6. 组装返回（保持前端接口不变）
    detail = {
        "id": video.id,
        "title": video.title,
        "description": video.description,
        "file_path": video.file_path,
        "cover_image": video.cover_image,
        "duration": video.duration,
        "view_count": video.view_count,
        "like_count": like_count,
        "collect_count": collect_count,
        "comment_count": comment_count,
        "created_at": video.created_at,
        "uploader": uploader_info,
        "is_liked": is_liked,
        "is_collected": is_collected
    }
    return detail


def video_to_dict(video):
    return {
        'id': video.id,
        'title': video.title,
        'description': video.description,
        'file_path': video.file_path,
        'cover_image': video.cover_image,
        'duration': video.duration,
        'uploader_id': video.uploader_id,
        'uploader_username': getattr(video.uploader, 'username', None) if hasattr(video, 'uploader') else None,
        'is_public': video.is_public,
        'is_deleted': video.is_deleted,
        'view_count': video.view_count,
        'like_count': video.like_count,
        'collect_count': video.collect_count,
        'comment_count': video.comment_count,
        'created_at': video.created_at,
        'updated_at': video.updated_at,
    }


async def get_my_like_video_list(db, user_id: int, page: int, size: int):
    stmt = (
        select(Video)
        .join(Like, Like.video_id == Video.id)
        .where(Like.user_id == user_id)
        .order_by(Like.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .options(joinedload(Video.uploader))
    )
    result = await db.execute(stmt)
    videos = result.scalars().unique().all()
    return [video_to_dict(v) for v in videos]


async def get_my_favorite_video_list(db, user_id: int, page: int, size: int):
    stmt = (
        select(Video)
        .join(Collection, Collection.video_id == Video.id)
        .where(Collection.user_id == user_id)
        .order_by(Collection.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .options(joinedload(Video.uploader))
    )
    result = await db.execute(stmt)
    videos = result.scalars().unique().all()
    return [video_to_dict(v) for v in videos]


async def get_latest_videos(db: AsyncSession, page: int, size: int = 20):
    skip = (page - 1) * size
    total, video_list = await get_latest_video_list(db=db, skip=skip, limit=size)
    items = [video_to_dict(v) for v in video_list]
    return {"total": total, "items": items}


async def get_hot_videos(db: AsyncSession, page: int, size: int = 20):
    skip = (page - 1) * size
    total, video_list = await get_hot_video_list(db=db, skip=skip, limit=size)
    items = [video_to_dict(v) for v in video_list]
    return {"total": total, "items": items}


async def get_following_feed_videos(db: AsyncSession, user_id: int, page: int, size: int = 20):
    # 1. 获取我关注的用户ID列表
    from app.crud.user.follow import get_following_list
    following = await get_following_list(db, user_id, 1, 10000)
    following_ids = [item['id'] for item in following['items']]
    if not following_ids:
        return {"total": 0, "items": []}
    # 2. 查询这些用户的视频
    skip = (page - 1) * size
    from sqlalchemy import select, desc
    from app.models.mysql.video import Video
    from sqlalchemy.orm import joinedload
    stmt = (
        select(Video)
        .options(joinedload(Video.uploader))
        .where(Video.uploader_id.in_(following_ids), Video.is_public == True, Video.is_deleted == False)
        .order_by(desc(Video.created_at))
        .offset(skip)
        .limit(size)
    )
    result = await db.execute(stmt)
    videos = result.scalars().unique().all()
    items = [video_to_dict(v) for v in videos]
    # 总数可选查一次
    return {"total": len(items), "items": items}

async def remove_video(
    db: AsyncSession,
    video_id: int,
    current_user_id: int,
):
    stmt = select(Video).where(Video.id == video_id, Video.is_deleted == False)
    result = await db.execute(stmt)
    video = result.scalars().first()

    if not video:
        return False, BizCode.NOT_FOUND, "视频不存在或已删除"

    if video.uploader_id != current_user_id:
        return False, BizCode.PERMISSION_DENIED, "无权限删除该视频"

    video.is_deleted = True
    video.is_public = False
    await db.commit()

    try:
        await log_user_behavior(
            user_id=current_user_id,
            action="delete",
            target_type="video",
            target_id=video_id,
            metadata={"title": video.title},
        )
    except Exception:
        pass

    return True, BizCode.SUCCESS, "视频已删除"

import os
from uuid import uuid4
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import settings
from app.crud.video import count_user_videos
from app.models.mysql.user import User
from app.crud.user.user import update_user_profile_picture, check_password, update_password
from app.schemas.user.profile import UserProfileResponse
from app.utils.file_validator import validate_image
from app.storage.local import save_file_to_local
from app.services.user.follow_service import get_following_count_service, get_fans_count_service
from datetime import datetime, timezone

# 用户头像存储目录（相对于MEDIA_ROOT）
AVATAR_DIR = os.path.join(settings.MEDIA_ROOT, "avatars")

async def save_user_avatar(db: AsyncSession, file: UploadFile, user_id: int) -> str:
    """
    校验上传文件是否为合法图片并保存为用户头像。
    - 验证文件类型和大小
    - 生成唯一文件名
    - 保存文件到本地存储路径
    - 更新用户数据库中的头像路径字段（相对路径）

    Args:
        db: 异步数据库会话
        file: 上传文件对象
        user_id: 用户ID

    Returns:
        str: 头像相对路径
    """
    validate_image(file)  # 校验上传文件是否合法（类型、大小）

    # 生成唯一文件名，格式：user_{user_id}_{uuid}.jpg
    filename = f"user_{user_id}_{uuid4().hex}.jpg"
    relative_path = os.path.join(AVATAR_DIR, filename)  # 存储时用相对路径
    full_path = os.path.join(f"{settings.media_root_abs}/avatars", filename)  # 绝对路径

    # 异步保存文件到本地磁盘
    await save_file_to_local(file, full_path)

    # 更新数据库用户头像字段，存储相对路径
    await update_user_profile_picture(db=db, user_id=user_id, path=relative_path)

    return relative_path


async def get_user_profile_with_stats(db: AsyncSession, user: User) -> UserProfileResponse:
    """
    查询用户信息及相关统计数据，组装返回用户资料响应体。

    Args:
        db: 异步数据库会话
        user: 用户模型实例

    Returns:
        UserProfileResponse: 包含用户基础信息和视频数量的响应模型
    """
    # 查询用户发布视频总数
    video_count = await count_user_videos(db, user.id)

    # 查询关注数和粉丝数
    following_count = await get_following_count_service(db, user.id)
    follower_count = await get_fans_count_service(db, user.id)

    # 构造返回对象，profile_picture字段有默认头像兜底
    return UserProfileResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        profile_picture=user.profile_picture or "/media/avatars/default.png",
        bio=user.bio,
        gender=user.gender,
        full_name=user.full_name,
        is_verified=user.is_verified,
        vip_level=user.vip_level,
        vip_expire_at=user.vip_expire_at,
        level=user.level,
        created_at=user.created_at,
        unique_id=user.unique_id,
        video_count=video_count,
        following_count=following_count,
        follower_count=follower_count
    )

async def change_password(db, user, old_password: str, new_password: str):
    from app.utils.security import verify_password, hash_password
    if not verify_password(old_password, user.password):
        raise ValueError("旧密码错误")
    user.password = hash_password(new_password)
    user.password_updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)

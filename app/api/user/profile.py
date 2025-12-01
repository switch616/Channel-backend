from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.mysql import get_db
from app.crud import update_user_profile
from app.schemas.http.response import ResponseSchema
from app.schemas.user.profile import UserProfileResponse, UserProfileUpdate
from app.models.mysql.user import User
from app.dependencies import get_current_user
from app.services.user.profile_service import (
    save_user_avatar,
    get_user_profile_with_stats
)

from app.schemas.user.auth import ChangePasswordRequest
from app.services.user.profile_service import change_password
from fastapi import HTTPException
from app.crud.user.user import get_user_by_id
from app.services.video.video import get_my_video_list

router = APIRouter()


@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取当前用户资料信息（附带视频统计）：
    - 查询基础信息 + 视频上传总数
    - 用于个人中心数据展示
    """
    return await get_user_profile_with_stats(db, current_user)


@router.get("/profile/{user_id}", response_model=ResponseSchema)
async def get_other_user_profile(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取其他用户资料信息（附带视频统计和关注状态）：
    - 查询指定用户的基础信息 + 视频上传总数
    - 同时返回当前用户对该用户的关注状态
    - 用于他人主页数据展示，减少API请求次数
    """
    # 获取指定用户
    target_user = await get_user_by_id(db, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 获取用户资料和统计数据
    user_profile = await get_user_profile_with_stats(db, target_user)
    
    # 获取关注状态
    is_followed = False
    is_mutual = False
    is_follower = False
    
    if user_id != current_user.id:  # 不能关注自己
        # 检查当前用户是否关注了目标用户
        from app.services.user.follow_service import is_following_service
        is_followed = await is_following_service(db, current_user.id, user_id)
        
        # 检查目标用户是否也关注了当前用户
        is_follower = await is_following_service(db, user_id, current_user.id)
        
        # 如果双方都关注了对方，则为互相关注
        if is_followed and is_follower:
            is_mutual = True
    
    # 将用户资料转换为字典，添加关注状态
    profile_dict = user_profile.model_dump()
    profile_dict.update({
        'is_followed': is_followed,
        'is_mutual': is_mutual,
        'is_follower': is_follower
    })
    
    return ResponseSchema.success(data=profile_dict)


@router.post("/upload-avatar", response_model=ResponseSchema)
async def upload_avatar(
    file: UploadFile = File(..., description="上传的头像文件"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    上传用户头像：
    - 校验图片格式、大小
    - 自动命名并存储到本地 / 云存储
    - 更新数据库中的头像字段（保存相对路径）
    """
    url = await save_user_avatar(db, file, current_user.id)
    return ResponseSchema.success(data={"url": url})


@router.post("/update-profile", response_model=ResponseSchema)
async def update_profile(
    profile: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    更新用户个人资料：
    - 支持修改用户名、性别、简介等字段
    - 若用户不存在则返回 404 异常
    """
    updated_user = await update_user_profile(db, current_user.id, {
        "username": profile.username,
        "bio": profile.bio,
        "gender": profile.gender,
    })
    if not updated_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return ResponseSchema.success(data="资料更新成功！")


@router.post("/change_password")
async def change_password_api(
    req: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    try:
        await change_password(db, user, req.old_password, req.new_password)
        return {"msg": "密码修改成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/profile/{user_id}", response_model=UserProfileResponse)
async def get_user_profile_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    获取指定用户资料信息（用于他人主页）
    """
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return await get_user_profile_with_stats(db, user)

@router.get("/{user_id}/videos", response_model=ResponseSchema)
async def get_user_videos(
    user_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(8, le=50),
    db: AsyncSession = Depends(get_db),
):
    """
    获取指定用户的作品列表
    """
    data = await get_my_video_list(db, user_id, page, size)
    return ResponseSchema.success(data=data)

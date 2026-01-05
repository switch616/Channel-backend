from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user
from app.schemas.http.response import ResponseSchema
from app.services import get_my_video_list, get_recommended_videos
from app.services.video.video import get_video_detail, get_latest_videos, get_hot_videos

router = APIRouter()

@router.get("/my_list", response_model=ResponseSchema)
async def my_list(
    page: int = Query(1, ge=1, description="分页页码，从 1 开始"),
    size: int = Query(20, le=50, description="每页数量，最大不超过 50"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    获取当前登录用户的视频列表
    - 支持分页查询
    - 返回用户本人上传的视频记录（不含逻辑删除/违规下架等）
    """
    data = await get_my_video_list(db, current_user.id, page, size)
    return ResponseSchema.success(data=data)


@router.get("/recommend", response_model=ResponseSchema)
async def recommend_videos(
    page: int = Query(1, ge=1, description="分页页码，从 1 开始"),
    size: int = Query(20, le=50, description="每页数量，最大不超过 50"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取推荐视频列表
    - 可作为首页 feed 使用
    - 当前实现为简单推荐（后续可对接推荐系统）
    - 支持分页
    """
    data = await get_recommended_videos(db, page=page, size=size)
    return ResponseSchema.success(data=data)


@router.get("/detail/{id}", response_model=ResponseSchema)
async def video_detail(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    获取指定视频的详细信息
    """
    detail = await get_video_detail(db, id, getattr(current_user, 'id', None))
    if not detail:
        return ResponseSchema.fail(msg="视频不存在")
    return ResponseSchema.success(data=detail)


@router.get("/latest", response_model=ResponseSchema)
async def latest_videos(
    page: int = Query(1, ge=1, description="分页页码，从 1 开始"),
    size: int = Query(20, le=50, description="每页数量，最大不超过 50"),
    db: AsyncSession = Depends(get_db),
):
    """获取最新视频列表"""
    data = await get_latest_videos(db, page, size)
    return ResponseSchema.success(data=data)


@router.get("/hot", response_model=ResponseSchema)
async def hot_videos(
    page: int = Query(1, ge=1, description="分页页码，从 1 开始"),
    size: int = Query(20, le=50, description="每页数量，最大不超过 50"),
    db: AsyncSession = Depends(get_db),
):
    """获取热门视频列表"""
    data = await get_hot_videos(db, page, size)
    return ResponseSchema.success(data=data)


@router.get("/following_feed", response_model=ResponseSchema)
async def following_feed(
    page: int = Query(1, ge=1, description="分页页码，从 1 开始"),
    size: int = Query(20, le=50, description="每页数量，最大不超过 50"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    获取我关注的用户的视频流
    """
    from app.services.video.video import get_following_feed_videos
    data = await get_following_feed_videos(db, current_user.id, page, size)
    return ResponseSchema.success(data=data)

@router.delete("/{video_id}", response_model=ResponseSchema)
async def delete_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    删除（下线）当前用户上传的视频
    - 软删除
    - 仅允许删除本人视频
    """

    from app.services.video.video import remove_video

    success, code, msg = await remove_video(
        db=db,
        video_id=video_id,
        current_user_id=current_user.id,
    )

    if not success:
        return ResponseSchema.fail(
            code=code,
            msg=msg,
        )

    return ResponseSchema.success(
        msg=msg,
    )

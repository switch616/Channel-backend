from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies import get_db, get_current_user
from app.schemas.response import ResponseSchema
from app.schemas.interaction.interaction import LikeCreate, CollectionCreate
from app.services.interaction.interaction import (
    toggle_video_like_service,
    toggle_video_collection_service,
    get_video_interaction_status
)
from app.services.video.video import get_my_like_video_list, get_my_favorite_video_list
from app.models.mysql.like import Like
from app.models.mysql.collection import Collection

router = APIRouter()


@router.post("/like", response_model=ResponseSchema)
async def toggle_like(
    like_data: LikeCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """切换视频点赞状态"""
    try:
        result = await toggle_video_like_service(db, like_data.video_id, current_user.id)
        return ResponseSchema.success(data=result, msg=result["message"])
    except Exception as e:
        return ResponseSchema.fail(msg=f"点赞操作失败: {str(e)}")


@router.post("/collection", response_model=ResponseSchema)
async def toggle_collection(
    collection_data: CollectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """切换视频收藏状态"""
    try:
        result = await toggle_video_collection_service(db, collection_data.video_id, current_user.id)
        return ResponseSchema.success(data=result, msg=result["message"])
    except Exception as e:
        return ResponseSchema.fail(msg=f"收藏操作失败: {str(e)}")


@router.get("/video/{video_id}/status", response_model=ResponseSchema)
async def get_interaction_status(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取视频交互状态（点赞、收藏）"""
    try:
        status = await get_video_interaction_status(db, video_id, current_user.id)
        return ResponseSchema.success(data=status)
    except Exception as e:
        return ResponseSchema.fail(msg=f"获取交互状态失败: {str(e)}")


@router.get("/my_likes", response_model=ResponseSchema)
async def my_likes(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取我点赞的视频列表"""
    data = await get_my_like_video_list(db, current_user.id, page, size)
    return ResponseSchema.success(data=data)


@router.get("/my_collections", response_model=ResponseSchema)
async def my_collections(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取我收藏的视频列表"""
    data = await get_my_favorite_video_list(db, current_user.id, page, size)
    return ResponseSchema.success(data=data)


@router.delete("/like/{video_id}", response_model=ResponseSchema)
async def delete_like(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """删除点赞（取消点赞）"""
    like = await db.scalar(select(Like).where(Like.video_id == video_id, Like.user_id == current_user.id))
    if not like:
        return ResponseSchema.fail(msg="未找到点赞记录")
    await db.delete(like)
    await db.commit()
    return ResponseSchema.success(msg="已取消点赞")

@router.delete("/collection/{video_id}", response_model=ResponseSchema)
async def delete_collection(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """删除收藏（取消收藏）"""
    collection = await db.scalar(select(Collection).where(Collection.video_id == video_id, Collection.user_id == current_user.id))
    if not collection:
        return ResponseSchema.fail(msg="未找到收藏记录")
    await db.delete(collection)
    await db.commit()
    return ResponseSchema.success(msg="已取消收藏") 
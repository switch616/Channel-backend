from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, get_current_user
from app.schemas.http.response import ResponseSchema
from app.schemas.user.follow import FollowRequest, FollowStatusResponse, FansCountResponse, FollowingCountResponse, FollowListResponse
from app.services.user.follow_service import (
    toggle_follow_service, is_following_service, get_fans_count_service, get_following_count_service,
    get_following_list_service, get_fans_list_service
)

router = APIRouter()

@router.post('/follow', response_model=ResponseSchema)
async def follow_user(
    req: FollowRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if req.user_id == current_user.id:
        return ResponseSchema.error(msg='不能关注自己')
    result = await toggle_follow_service(db, current_user.id, req.user_id)
    
    # 获取操作后的统计数据
    following_count = await get_following_count_service(db, current_user.id)
    follower_count = await get_fans_count_service(db, current_user.id)
    
    # 检查对方是否关注了当前用户
    is_follower = await is_following_service(db, req.user_id, current_user.id)
    
    # 检查互相关注状态
    is_mutual = result and is_follower
    
    return ResponseSchema.success(
        data={
            'is_followed': result,
            'is_mutual': is_mutual,
            'is_follower': is_follower,
            'following_count': following_count,
            'follower_count': follower_count
        }, 
        msg='关注成功' if result else '取消关注成功'
    )

@router.get('/follow_status', response_model=ResponseSchema)
async def follow_status(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if user_id == current_user.id:
        return ResponseSchema.success(data={
            'is_followed': False,
            'is_mutual': False,
            'is_follower': False
        })
    
    # 检查当前用户是否关注了目标用户
    is_followed = await is_following_service(db, current_user.id, user_id)
    
    # 检查目标用户是否也关注了当前用户
    is_follower = await is_following_service(db, user_id, current_user.id)
    
    # 检查互相关注状态
    is_mutual = is_followed and is_follower
    
    return ResponseSchema.success(data={
        'is_followed': is_followed,
        'is_mutual': is_mutual,
        'is_follower': is_follower
    })

@router.get('/fans_count', response_model=FansCountResponse)
async def fans_count(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    count = await get_fans_count_service(db, user_id)
    return FansCountResponse(fans_count=count)

@router.get('/following_count', response_model=FollowingCountResponse)
async def following_count(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    count = await get_following_count_service(db, user_id)
    return FollowingCountResponse(following_count=count)

@router.get('/following_list', response_model=ResponseSchema)
async def following_list(
    user_id: int,
    page: int = 1,
    size: int = 20,
    search: str = '',
    order: str = 'desc',
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    print(f"[DEBUG] /user/following_list user_id={user_id}")
    data = await get_following_list_service(db, user_id, page, size, search, order, current_user.id)
    return ResponseSchema.success(data=data)

@router.get('/fans_list', response_model=ResponseSchema)
async def fans_list(
    user_id: int,
    page: int = 1,
    size: int = 20,
    search: str = '',
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    print(f"[DEBUG] /user/fans_list user_id={user_id}")
    data = await get_fans_list_service(db, user_id, page, size, search, current_user.id)
    return ResponseSchema.success(data=data)

@router.post('/remove_follow', response_model=ResponseSchema)
async def remove_follow(
    req: FollowRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """移除关注（从关注列表中移除）"""
    if req.user_id == current_user.id:
        return ResponseSchema.error(msg='不能移除自己')
    
    # 检查是否真的关注了该用户
    is_followed = await is_following_service(db, current_user.id, req.user_id)
    if not is_followed:
        return ResponseSchema.error(msg='您没有关注该用户')
    
    # 取消关注
    result = await toggle_follow_service(db, current_user.id, req.user_id)
    
    # 获取操作后的统计数据
    following_count = await get_following_count_service(db, current_user.id)
    follower_count = await get_fans_count_service(db, current_user.id)
    
    return ResponseSchema.success(
        data={
            'is_followed': False,
            'following_count': following_count,
            'follower_count': follower_count
        }, 
        msg='移除关注成功'
    )

@router.post('/remove_fan', response_model=ResponseSchema)
async def remove_fan(
    req: FollowRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """移除粉丝（从粉丝列表中移除）"""
    if req.user_id == current_user.id:
        return ResponseSchema.error(msg='不能移除自己')
    
    # 检查该用户是否真的是当前用户的粉丝
    is_fan = await is_following_service(db, req.user_id, current_user.id)
    if not is_fan:
        return ResponseSchema.error(msg='该用户不是您的粉丝')
    
    # 取消该用户对当前用户的关注（移除粉丝）
    result = await toggle_follow_service(db, req.user_id, current_user.id)
    
    # 获取操作后的统计数据
    following_count = await get_following_count_service(db, current_user.id)
    follower_count = await get_fans_count_service(db, current_user.id)
    
    return ResponseSchema.success(
        data={
            'removed': True,
            'following_count': following_count,
            'follower_count': follower_count
        }, 
        msg='移除粉丝成功'
    ) 
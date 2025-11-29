from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.comment.comment import (
    create_comment,
    get_video_comments,
    get_comment_reply_count,
    delete_comment,
    toggle_comment_interaction,
    get_user_comment_interaction,
    get_comment_tree,
    delete_comment_with_permission
)
from app.schemas.comment.comment import CommentCreate, CommentOut, CommentListResponse
from app.models.mysql.comment import Comment
from app.models.mysql.video import Video


async def create_video_comment(
    db: AsyncSession, 
    comment_data: CommentCreate, 
    user_id: int
) -> CommentOut:
    """创建视频评论"""
    # 创建评论
    comment = await create_comment(db, comment_data, user_id)
    
    # 获取回复数量（只对一级评论计算）
    reply_count = 0
    if comment_data.parent_id is None:  # 一级评论
        reply_count = await get_comment_reply_count(db, comment.id)
    
    # 组装返回数据
    return CommentOut(
        id=comment.id,
        content=comment.content,
        like_count=comment.like_count,
        dislike_count=comment.dislike_count,
        created_at=comment.created_at,
        user={
            "id": comment.user.id,
            "username": comment.user.username,
            "profile_picture": comment.user.profile_picture
        },
        parent_id=comment.parent_id,
        reply_count=reply_count
    )


async def get_video_comment_list(
    db: AsyncSession,
    video_id: int,
    page: int = 1,
    size: int = 20,
    parent_id: Optional[int] = None,
    order: str = "latest"
) -> CommentListResponse:
    """获取视频评论列表"""
    skip = (page - 1) * size
    total, comments = await get_video_comments(db, video_id, skip, size, parent_id, order)
    
    # 组装评论列表
    items = []
    for comment in comments:
        # 获取回复数量（对所有评论都计算）
        reply_count = await get_comment_reply_count(db, comment.id)
        
        comment_out = CommentOut(
            id=comment.id,
            content=comment.content,
            like_count=comment.like_count,
            dislike_count=comment.dislike_count,
            created_at=comment.created_at,
            user={
                "id": comment.user.id,
                "username": comment.user.username,
                "profile_picture": comment.user.profile_picture
            },
            parent_id=comment.parent_id,
            reply_count=reply_count
        )
        items.append(comment_out)
    
    return CommentListResponse(total=total, items=items)


async def toggle_comment_like_dislike(
    db: AsyncSession,
    comment_id: int,
    user_id: int,
    is_like: bool
) -> dict:
    """切换评论点赞/踩状态"""
    success = await toggle_comment_interaction(db, comment_id, user_id, is_like)
    
    if success:
        # 获取更新后的点赞/踩数
        comment = await db.get(Comment, comment_id)
        return {
            "success": True,
            "message": "操作成功",
            "like_count": comment.like_count,
            "dislike_count": comment.dislike_count
        }
    else:
        return {
            "success": False,
            "message": "操作失败",
            "like_count": 0,
            "dislike_count": 0
        }


async def delete_user_comment(
    db: AsyncSession,
    comment_id: int,
    user_id: int
) -> bool:
    """删除用户评论"""
    return await delete_comment(db, comment_id, user_id) 


async def build_comment_tree(comment) -> tuple:
    """递归组装评论树并统计所有子评论数量"""
    children = getattr(comment, 'children', [])
    reply_count = 0
    children_out = []
    for child in children:
        child_out, child_reply_count = await build_comment_tree(child)
        children_out.append(child_out)
        reply_count += 1 + child_reply_count
    comment_out = {
        "id": comment.id,
        "content": comment.content,
        "like_count": comment.like_count,
        "dislike_count": comment.dislike_count,
        "created_at": comment.created_at,
        "user": {
            "id": comment.user.id,
            "username": comment.user.username,
            "profile_picture": comment.user.profile_picture
        },
        "parent_id": comment.parent_id,
        "reply_count": reply_count,
        "children": children_out
    }
    return comment_out, reply_count


async def get_video_comment_tree(db: AsyncSession, video_id: int) -> list:
    """获取视频评论树"""
    comments = await get_comment_tree(db, video_id, None)
    tree = []
    for comment in comments:
        comment_out, _ = await build_comment_tree(comment)
        tree.append(comment_out)
    return tree


async def delete_comment_service(db: AsyncSession, comment_id: int, user_id: int) -> bool:
    # 获取评论
    comment = await db.get(Comment, comment_id)
    if not comment:
        return False
    # 获取视频
    video = await db.get(Video, comment.video_id)
    if not video:
        return False
    return await delete_comment_with_permission(db, comment_id, user_id, video.uploader_id) 
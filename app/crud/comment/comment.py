from typing import List, Optional, Tuple
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import select, func, desc, delete

from app.models.mysql.comment import Comment
from app.models.mysql.comment_interaction import CommentInteraction
from app.schemas.comment.comment import CommentCreate


async def create_comment(db: AsyncSession, comment_data: CommentCreate, user_id: int) -> Comment:
    """创建评论"""
    db_comment = Comment(
        video_id=comment_data.video_id,
        user_id=user_id,
        content=comment_data.content,
        parent_id=comment_data.parent_id
    )
    db.add(db_comment)
    await db.commit()
    await db.refresh(db_comment)
    return db_comment


async def get_video_comments(
    db: AsyncSession, 
    video_id: int, 
    skip: int = 0, 
    limit: int = 20,
    parent_id: Optional[int] = None,
    order: str = "latest"
) -> Tuple[int, List[Comment]]:
    """获取视频评论列表"""
    # 查询条件
    where_conditions = [Comment.video_id == video_id]
    if parent_id is not None:
        where_conditions.append(Comment.parent_id == parent_id)
    else:
        where_conditions.append(Comment.parent_id.is_(None))  # 只查询一级评论
    
    # 查询总数
    total_stmt = select(func.count(Comment.id)).where(*where_conditions)
    total = await db.scalar(total_stmt)
    
    # 查询评论列表，预加载用户信息
    if order == "hottest":
        # 按热度排序（点赞数）
        stmt = (
            select(Comment)
            .options(joinedload(Comment.user))
            .where(*where_conditions)
            .order_by(desc(Comment.like_count), desc(Comment.created_at))
            .offset(skip)
            .limit(limit)
        )
    else:
        # 按最新排序（默认）
        stmt = (
            select(Comment)
            .options(joinedload(Comment.user))
            .where(*where_conditions)
            .order_by(desc(Comment.created_at))
            .offset(skip)
            .limit(limit)
        )
    result = await db.execute(stmt)
    comments = result.scalars().unique().all()
    
    return total, comments


async def get_comment_reply_count(db: AsyncSession, comment_id: int) -> int:
    """获取评论的回复数量（包括所有子级回复）"""
    # 递归获取所有子评论的数量
    async def count_all_replies(parent_id: int) -> int:
        # 获取直接回复
        direct_replies = await db.scalar(
            select(func.count(Comment.id)).where(Comment.parent_id == parent_id)
        ) or 0
        
        # 递归获取每个直接回复的子回复
        total = direct_replies
        if direct_replies > 0:
            # 获取所有直接回复的ID
            result = await db.execute(
                select(Comment.id).where(Comment.parent_id == parent_id)
            )
            child_ids = [row[0] for row in result.fetchall()]
            
            # 递归计算每个子评论的回复数量
            for child_id in child_ids:
                total += await count_all_replies(child_id)
        
        return total
    
    return await count_all_replies(comment_id)


async def get_comment_by_id(db: AsyncSession, comment_id: int) -> Optional[Comment]:
    """根据ID获取评论"""
    result = await db.execute(
        select(Comment).options(joinedload(Comment.user)).where(Comment.id == comment_id)
    )
    return result.scalars().first()


async def delete_comment(db: AsyncSession, comment_id: int, user_id: int) -> bool:
    """删除评论（只能删除自己的评论）"""
    result = await db.execute(
        select(Comment).where(Comment.id == comment_id, Comment.user_id == user_id)
    )
    comment = result.scalars().first()
    if comment:
        await db.delete(comment)
        await db.commit()
        return True
    return False


async def update_comment_like_count(db: AsyncSession, comment_id: int) -> None:
    """更新评论点赞数"""
    like_count = await db.scalar(
        select(func.count(CommentInteraction.id))
        .where(CommentInteraction.comment_id == comment_id, CommentInteraction.is_like == True)
    )
    
    dislike_count = await db.scalar(
        select(func.count(CommentInteraction.id))
        .where(CommentInteraction.comment_id == comment_id, CommentInteraction.is_like == False)
    )
    
    # 更新评论的点赞和踩数
    await db.execute(
        select(Comment).where(Comment.id == comment_id)
    )
    comment = await db.scalar(select(Comment).where(Comment.id == comment_id))
    if comment:
        comment.like_count = like_count or 0
        comment.dislike_count = dislike_count or 0
        await db.commit()


async def toggle_comment_interaction(
    db: AsyncSession, 
    comment_id: int, 
    user_id: int, 
    is_like: bool
) -> bool:
    """切换评论点赞/踩状态"""
    # 检查是否已存在交互记录
    existing = await db.scalar(
        select(CommentInteraction).where(
            CommentInteraction.comment_id == comment_id,
            CommentInteraction.user_id == user_id
        )
    )
    
    if existing:
        if existing.is_like == is_like:
            # 取消操作
            await db.delete(existing)
        else:
            # 切换操作类型
            existing.is_like = is_like
    else:
        # 创建新的交互记录
        interaction = CommentInteraction(
            comment_id=comment_id,
            user_id=user_id,
            is_like=is_like
        )
        db.add(interaction)
    
    await db.commit()
    
    # 更新评论的点赞/踩数
    await update_comment_like_count(db, comment_id)
    
    return True


async def get_user_comment_interaction(
    db: AsyncSession, 
    comment_id: int, 
    user_id: int
) -> Optional[CommentInteraction]:
    """获取用户对评论的交互状态"""
    result = await db.scalar(
        select(CommentInteraction).where(
            CommentInteraction.comment_id == comment_id,
            CommentInteraction.user_id == user_id
        )
    )
    return result 


async def get_comment_tree(db: AsyncSession, video_id: int, parent_id: Optional[int] = None) -> List[Comment]:
    """递归获取评论树"""
    stmt = (
        select(Comment)
        .options(joinedload(Comment.user))
        .where(Comment.video_id == video_id)
        .where(Comment.parent_id == parent_id)
        .order_by(Comment.created_at.asc())
    )
    result = await db.execute(stmt)
    comments = result.scalars().unique().all()
    for comment in comments:
        comment.children = await get_comment_tree(db, video_id, comment.id)
    return comments


async def delete_comment_and_children(db: AsyncSession, comment_id: int):
    # 递归删除所有子评论
    children = await db.execute(select(Comment.id).where(Comment.parent_id == comment_id))
    child_ids = [row[0] for row in children.fetchall()]
    for cid in child_ids:
        await delete_comment_and_children(db, cid)
    
    # 删除当前评论的所有交互记录（点赞/踩）
    await db.execute(
        delete(CommentInteraction).where(CommentInteraction.comment_id == comment_id)
    )
    
    # 删除评论本身
    comment = await db.get(Comment, comment_id)
    if comment:
        await db.delete(comment)
        await db.commit()


async def delete_comment_with_permission(db: AsyncSession, comment_id: int, user_id: int, video_owner_id: int) -> bool:
    """视频所有者可删除任意评论，普通用户只能删除自己评论，递归删除所有子评论"""
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalars().first()
    if not comment:
        return False
    if comment.user_id == user_id or video_owner_id == user_id:
        await delete_comment_and_children(db, comment_id)
        return True
    return False 
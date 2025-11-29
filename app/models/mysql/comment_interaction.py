from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.sql import func
from app.models.mysql.base import Base


class CommentInteraction(Base):
    __tablename__ = 'comment_interactions'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)        # 用户ID
    comment_id = Column(Integer, ForeignKey("comments.id"), nullable=False)  # 评论ID
    is_like = Column(Boolean, nullable=False)                                # True为点赞，False为踩

    created_at = Column(DateTime, default=func.now())                        # 创建时间

    __table_args__ = (
        UniqueConstraint("user_id", "comment_id", name="uq_user_comment_interaction"),  # 防止重复操作
    )

    def __repr__(self):
        action = "like" if self.is_like else "dislike"
        return f"<CommentInteraction user={self.user_id} comment={self.comment_id} action={action}>" 
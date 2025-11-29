from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from app.models.mysql.base import Base

class Follow(Base):
    __tablename__ = 'follows'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # 关注者
    followed_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # 被关注者
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'followed_user_id', name='uq_user_followed'),
    )

    def __repr__(self):
        return f"<Follow user={self.user_id} follow={self.followed_user_id}>" 
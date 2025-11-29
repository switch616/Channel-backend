from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from app.models.mysql.base import Base


class Collection(Base):
    __tablename__ = 'collections'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)        # 收藏者
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)      # 被收藏视频

    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "video_id", name="uq_user_video_collect"),  # 防止重复收藏
    )

    def __repr__(self):
        return f"<Collection user={self.user_id} video={self.video_id}>"

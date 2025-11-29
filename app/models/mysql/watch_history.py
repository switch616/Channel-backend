from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.models.mysql.base import Base


class WatchHistory(Base):
    __tablename__ = 'watch_history'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)        # 用户 ID
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)      # 视频 ID
    watch_time = Column(Integer, default=0)                                  # 已观看时长（秒）
    last_watch_at = Column(DateTime, default=func.now())                     # 最后观看时间

    def __repr__(self):
        return f"<WatchHistory user={self.user_id} video={self.video_id} time={self.watch_time}>"

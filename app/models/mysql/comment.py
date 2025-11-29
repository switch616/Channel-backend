from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.mysql.base import Base


class Comment(Base):
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)      # 关联视频
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)        # 评论用户
    content = Column(Text, nullable=False)                                   # 评论内容
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True)    # 嵌套评论（父级）

    like_count = Column(Integer, default=0)                                  # 点赞数
    dislike_count = Column(Integer, default=0)                               # 踩数

    created_at = Column(DateTime, default=func.now())                        # 创建时间

    # ORM 关系
    video = relationship("Video", backref="comments")
    user = relationship("User", backref="comments")
    replies = relationship("Comment", backref="parent", remote_side=[id])

    def __repr__(self):
        return f"<Comment by User {self.user_id} on Video {self.video_id}>"

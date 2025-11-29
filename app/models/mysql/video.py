from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.mysql.base import Base


class Video(Base):
    __tablename__ = 'videos'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)  # 视频标题
    description = Column(Text, nullable=True)  # 视频描述
    file_path = Column(String(500), nullable=False)  # 视频文件路径
    cover_image = Column(String(500), nullable=True)  # 封面图片路径
    duration = Column(Integer, nullable=True)  # 视频时长（秒）

    uploader_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 上传者 ID
    uploader = relationship("User", backref="videos")  # ORM 反向关系

    is_public = Column(Boolean, default=True)  # 是否公开
    is_deleted = Column(Boolean, default=False)  # 逻辑删除标志位

    view_count = Column(Integer, default=0)  # 观看次数
    like_count = Column(Integer, default=0)  # 点赞数
    collect_count = Column(Integer, default=0)  # 收藏数
    comment_count = Column(Integer, default=0)  # 评论数

    def __repr__(self):
        return f"<Video {self.title}>"

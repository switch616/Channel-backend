from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# 视频基础字段，所有视频相关模型共用
class VideoBase(BaseModel):
    title: str  # 视频标题，必填
    description: Optional[str] = None  # 视频描述，可选
    file_path: str  # 视频文件路径，必填

# 创建视频请求体，继承基础字段，增加封面和时长
class VideoCreate(VideoBase):
    cover_image: Optional[str] = None  # 封面图片路径，可选
    duration: Optional[int] = None  # 视频时长（秒），可选

# 更新视频请求体，支持部分字段更新，全部可选
class VideoUpdate(BaseModel):
    title: Optional[str]  # 视频标题，可选
    description: Optional[str]  # 视频描述，可选

# 视频输出模型，包含数据库中额外字段，如ID，上传者，创建时间
class VideoOut(VideoBase):
    id: int  # 视频ID
    uploader_id: int  # 上传者用户ID
    created_at: datetime  # 创建时间

    class Config:
        from_attributes = True  # 支持ORM模型转换

# 我的上传视频列表项输出模型，字段更详细，包含点赞数及上传者信息
class MyVideoListOut(BaseModel):
    id: int  # 视频ID
    title: str  # 视频标题
    cover_image: Optional[str]  # 封面图片路径
    file_path: str  # 视频文件路径
    created_at: datetime  # 创建时间
    duration: int  # 视频时长（秒）
    like_count: int  # 点赞数量
    uploader_id: int  # 上传者ID
    uploader_username: str  # 上传者用户名
    uploader_unique_id: str  # 上传者唯一ID

    class Config:
        from_attributes = True  # 支持ORM模型转换

# 视频列表响应，包含总数及视频列表
class VideoListResponse(BaseModel):
    total: int  # 视频总数
    videos: List[VideoOut]  # 视频列表

# 推荐视频输出模型，类似于MyVideoListOut但结构更简洁
class RecommendVideoOut(BaseModel):
    id: int  # 视频ID
    title: str  # 视频标题
    cover_image: str  # 封面图片路径
    file_path: str  # 视频文件路径
    created_at: datetime  # 创建时间
    duration: int  # 视频时长（秒）

    uploader_id: int  # 上传者ID
    uploader_username: str  # 上传者用户名
    uploader_unique_id: str  # 上传者唯一ID

    like_count: int  # 点赞数

    class Config:
        from_attributes = True  # 支持ORM模型转换

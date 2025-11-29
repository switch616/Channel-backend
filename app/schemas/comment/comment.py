from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CommentBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=500, description="评论内容")


class CommentCreate(CommentBase):
    video_id: int = Field(..., description="视频ID")
    parent_id: Optional[int] = Field(None, description="父评论ID，用于回复")


class CommentUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=500, description="评论内容")


class CommentUserInfo(BaseModel):
    id: int
    username: str
    profile_picture: Optional[str] = None

    class Config:
        from_attributes = True


class CommentOut(BaseModel):
    id: int
    content: str
    like_count: int
    dislike_count: int
    created_at: datetime
    user: CommentUserInfo
    parent_id: Optional[int] = None
    reply_count: int = 0  # 回复数量

    class Config:
        from_attributes = True


class CommentListResponse(BaseModel):
    total: int
    items: List[CommentOut]


class CommentInteractionCreate(BaseModel):
    comment_id: int = Field(..., description="评论ID")
    is_like: bool = Field(..., description="True为点赞，False为踩")


class CommentInteractionResponse(BaseModel):
    success: bool
    message: str
    like_count: int
    dislike_count: int 
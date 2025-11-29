from pydantic import BaseModel, Field
from typing import Optional


class LikeCreate(BaseModel):
    video_id: int = Field(..., description="视频ID")


class LikeResponse(BaseModel):
    success: bool
    message: str
    like_count: int


class CollectionCreate(BaseModel):
    video_id: int = Field(..., description="视频ID")


class CollectionResponse(BaseModel):
    success: bool
    message: str
    collect_count: int


class VideoInteractionStatus(BaseModel):
    is_liked: bool
    is_collected: bool
    like_count: int
    collect_count: int 
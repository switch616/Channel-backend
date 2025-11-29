from typing import List, Optional
from pydantic import BaseModel

class FollowRequest(BaseModel):
    user_id: int  # 被关注者ID

class FollowStatusResponse(BaseModel):
    is_followed: bool
    is_mutual: bool

class FansCountResponse(BaseModel):
    fans_count: int

class FollowingCountResponse(BaseModel):
    following_count: int

class FollowUserInfo(BaseModel):
    id: int
    username: str
    unique_id: str
    profile_picture: Optional[str]
    created_at: str

class FollowListResponse(BaseModel):
    total: int
    items: List[FollowUserInfo] 
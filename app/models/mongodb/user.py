from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class UserBehaviorLog(BaseModel):
    """用户行为日志"""
    user_id: int
    action: str  # watch, like, comment, search, etc.
    target_type: str  # video, comment, user, etc.
    target_id: int
    metadata: Dict[str, Any] = {}  # 额外信息
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        collection = "user_behaviors"


class UserPreference(BaseModel):
    """用户偏好数据"""
    user_id: int
    categories: List[str] = []  # 感兴趣的分类
    tags: List[str] = []  # 感兴趣的标签
    watch_history: List[int] = []  # 观看过的视频ID
    like_history: List[int] = []  # 点赞过的视频ID
    search_history: List[str] = []  # 搜索历史
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        collection = "user_preferences"


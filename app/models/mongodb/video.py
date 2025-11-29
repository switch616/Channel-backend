from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class VideoViewHistory(BaseModel):
    """视频观看历史详情"""
    user_id: int
    video_id: int
    watch_duration: int  # 观看时长（秒）
    watch_progress: float  # 观看进度 0-1
    device_info: Dict[str, str] = {}  # 设备信息
    location: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        collection = "video_views"


class VideoAnalytics(BaseModel):
    """视频分析数据"""
    video_id: int
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    watch_time_total: int = 0  # 总观看时长
    viewer_retention: List[float] = []  # 观众留存率
    daily_stats: Dict[str, Dict[str, int]] = {}  # 每日统计
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        collection = "video_analytics"

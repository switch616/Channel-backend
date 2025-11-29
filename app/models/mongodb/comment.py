from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CommentContent(BaseModel):
    """评论内容（MongoDB存储）"""
    comment_id: int  # 对应MySQL的comment.id
    content: str
    rich_content: Optional[Dict[str, Any]] = None  # 富文本内容
    mentions: List[str] = []  # @提及的用户
    hashtags: List[str] = []  # 话题标签
    media_attachments: List[Dict[str, str]] = []  # 媒体附件
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        collection = "comment_contents"


from pydantic import BaseModel, constr, validator
from typing import Optional
from enum import Enum
import re
from datetime import datetime

# 性别枚举类，定义数据库中对应的性别字段选项
class GenderEnum(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"

# 用户资料响应模型，前端返回的用户详细信息结构
class UserProfileResponse(BaseModel):
    id: int  # 用户ID
    username: str  # 用户名
    email: str  # 邮箱
    profile_picture: str  # 头像URL
    bio: Optional[str]  # 个人简介，可选
    gender: str  # 性别
    full_name: Optional[str]  # 真实姓名，可选
    is_verified: bool  # 是否认证用户
    vip_level: int  # VIP等级
    vip_expire_at: Optional[datetime]  # VIP到期时间，可选
    level: int  # 用户等级
    created_at: datetime  # 账户创建时间
    unique_id: str  # 唯一标识符

    video_count: int  # 用户上传视频数量统计
    following_count: int  # 关注数
    follower_count: int   # 粉丝数

# 用户资料更新请求模型，用于验证前端提交的资料修改数据
class UserProfileUpdate(BaseModel):
    username: constr(min_length=1)  # 用户名，至少一个字符
    bio: str | None = None  # 个人简介，可为空
    gender: GenderEnum | None = None  # 性别，枚举类型，可为空

    # 校验用户名，只允许字母、数字、下划线和中文字符
    @validator('username')
    def username_no_special_chars(cls, v):
        if not re.match(r'^[\w\u4e00-\u9fa5]+$', v):
            raise ValueError('用户名只能包含字母、数字、下划线和中文')
        return v

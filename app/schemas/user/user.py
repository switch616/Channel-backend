from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
import re

# 通用基础配置类，启用Pydantic v2的 from_attributes 功能，支持ORM模型映射
class BaseConfigModel(BaseModel):
    model_config = {
        "from_attributes": True
    }

# 用户公共字段基类，包含用户入参与出参通用字段定义
class UserBase(BaseConfigModel):
    email: EmailStr  # 邮箱，使用EmailStr类型自动校验
    username: str  # 用户名
    first_name: Optional[str] = None  # 名
    last_name: Optional[str] = None  # 姓
    full_name: Optional[str] = None  # 全名
    bio: Optional[str] = None  # 个人简介
    phone_number: Optional[str] = Field(None, pattern=r'^1[3-9]\d{9}$')  # 手机号，匹配中国手机号格式
    address: Optional[str] = None  # 地址
    profile_picture: Optional[str] = None  # 头像URL
    city: Optional[str] = None  # 城市
    state: Optional[str] = None  # 省/州
    country: Optional[str] = None  # 国家
    postal_code: Optional[str] = None  # 邮编

# 用户注册请求体，继承自UserBase，增加密码及权限相关字段
class UserCreate(UserBase):
    password: str  # 密码，必填
    is_active: Optional[bool] = True  # 是否激活，默认激活
    is_verified: Optional[bool] = False  # 是否验证邮箱，默认未验证
    is_superuser: Optional[bool] = False  # 是否超级管理员，默认否

# 注册请求体，包含验证码字段，继承UserBase
class RegisterRequest(UserBase):
    password: str  # 密码
    code: str  # 验证码（如邮箱验证码）

# 用户更新请求体，所有字段均为可选，支持部分更新
class UserUpdate(UserBase):
    email: Optional[EmailStr] = None  # 邮箱（可选）
    username: Optional[str] = None  # 用户名（可选）
    # 其余字段继承自UserBase，均为可选

# 接口返回的用户信息，包含用户状态和时间戳字段
class UserResponse(UserBase):
    id: int  # 用户ID
    is_active: bool  # 是否激活
    is_verified: bool  # 是否已验证
    is_superuser: bool  # 是否管理员
    created_at: Optional[datetime]  # 账户创建时间
    updated_at: Optional[datetime]  # 账户更新时间

# 登录成功响应模型，限制返回信息，避免暴露敏感字段
class UserLoginResponse(BaseConfigModel):
    id: int  # 用户ID
    username: str  # 用户名
    access_token: str  # JWT访问令牌
    token_type: str = "bearer"  # token类型，固定为bearer

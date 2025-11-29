from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.sql import func
from app.models.mysql.base import Base
from enum import Enum
import uuid


# 添加性别枚举类
class GenderEnum(str, Enum):
    MALE = "male"  # 男
    FEMALE = "female"  # 女
    OTHER = "other"  # 其他
    UNKNOWN = "unknown"  # 未知/不愿透露


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)  # 主键，自增 ID
    # 用户标识码，唯一ID
    unique_id = Column(
        String(32),
        unique=True,
        index=True,
        nullable=False,
        default=lambda: str(uuid.uuid4().hex)[:16]  # 默认生成16位唯一ID
    )
    email = Column(String(255), unique=True, index=True, nullable=False)  # 用户邮箱，唯一
    username = Column(String(50), unique=True, index=True, nullable=False)  # 用户名，唯一
    password = Column(String(255), nullable=False)  # 加密后的用户密码

    # 用户基础信息
    first_name = Column(String(100), nullable=True)  # 名
    last_name = Column(String(100), nullable=True)  # 姓
    full_name = Column(String(200), nullable=True)  # 全名（可选字段）
    gender = Column(SQLEnum(GenderEnum), default=GenderEnum.MALE, nullable=False)  # 性别
    bio = Column(Text, nullable=True)  # 个人简介
    phone_number = Column(String(20), nullable=True)  # 手机号（用于通知/验证）
    profile_picture = Column(String(255), nullable=True, default='media/avatars/default.png')  # 用户头像路径

    # 地址信息
    address = Column(Text, nullable=True)  # 详细地址
    city = Column(String(100), nullable=True)  # 城市
    state = Column(String(100), nullable=True)  # 州/省份
    country = Column(String(100), nullable=True)  # 国家
    postal_code = Column(String(20), nullable=True)  # 邮政编码

    # 系统权限相关
    is_active = Column(Boolean, default=True)  # 是否激活账户（逻辑删除用）
    is_verified = Column(Boolean, default=False)  # 邮箱是否已验证
    is_superuser = Column(Boolean, default=False)  # 是否是超级管理员

    # 实名认证相关字段
    real_name = Column(String(100), nullable=True)  # 真实姓名
    id_number = Column(String(30), nullable=True)  # 身份证号（或其他 ID，脱敏加密存储）
    is_verified_realname = Column(Boolean, default=False)  # 是否通过实名认证

    # 用户成长体系
    level = Column(Integer, default=1)  # 用户等级（例如从 1 到 10）
    experience = Column(Integer, default=0)  # 经验值（升级依据）
    activity_score = Column(Float, default=0.0)  # 活跃度评分（用于推荐算法、用户画像等）

    # 用户登录行为
    login_count = Column(Integer, default=0)  # 登录次数（行为分析/成就系统）
    last_login_at = Column(DateTime, nullable=True)  # 上次登录时间

    # VIP 会员系统
    vip_level = Column(Integer, default=0)  # VIP 等级（0 表示非会员）
    vip_expire_at = Column(DateTime, nullable=True)  # VIP 到期时间

    # 风控字段
    is_banned = Column(Boolean, default=False)  # 是否被封禁
    ban_reason = Column(Text, nullable=True)  # 封禁原因（如有）

    # 密码更新时间
    password_updated_at = Column(DateTime, default=func.now(), nullable=False)  # 密码最后更新时间

    def __repr__(self):
        return f"<User {self.username} - {self.email}>"

"""
应用配置文件
使用 pydantic-settings 管理配置，支持从环境变量和 .env 文件加载
"""

import json
import os
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    应用配置类
    所有配置项都通过环境变量或 .env 文件设置
    """

    # ========== 数据库配置 ==========
    DB_USER: str = Field(description="数据库用户名")
    DB_PASSWORD: str = Field(description="数据库密码")
    DB_HOST: str = Field(description="数据库主机地址，例如 localhost 或 127.0.0.1")
    DB_PORT: int = Field(description="数据库端口号，默认 MySQL 为 3306")
    DB_NAME: str = Field(description="数据库名称")
    ASYNC_DB_DRIVER: str = Field(default="mysql+asyncmy", description="异步驱动（用于生产运行环境）")
    SYNC_DB_DRIVER: str = Field(default="mysql+mysqlconnector", description="同步驱动（用于数据库迁移）")

    # ========== Redis 配置 ==========
    REDIS_HOST: str = Field(description="Redis 主机地址，例如：localhost 或 redis-server")
    REDIS_PORT: int = Field(description="Redis 端口，默认一般是 6379")
    REDIS_PASSWORD: str = Field(default="", description="Redis 密码，如果Redis没有设置密码则留空")

    # ========== MongoDB 配置 ==========
    MONGODB_HOST: str = Field(description="MongoDB 主机地址，例如：localhost 或 127.0.0.1")
    MONGODB_PORT: int = Field(description="MongoDB 端口号，默认 27017")
    MONGODB_USER: str = Field(description="MongoDB 用户名")
    MONGODB_PASSWORD: str = Field(description="MongoDB 密码")
    MONGODB_DB: str = Field(description="MongoDB 数据库名称")
    MONGODB_AUTH_SOURCE: str = Field(default="admin", description="MongoDB 认证数据库，默认为 admin")

    # ========== JWT 鉴权配置 ==========
    SECRET_KEY: str = Field(description="用于加密 JWT 的密钥，必须保密")
    ALGORITHM: str = Field(description="JWT 加密算法，例如 HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(description="JWT 访问令牌过期时间（单位：分钟）")

    # ========== 邮箱服务配置（网易邮箱） ==========
    EMAIL_HOST: str = Field(description="邮件服务器地址，例如 smtp.163.com")
    EMAIL_PORT: str = Field(description="邮件服务器端口，通常是 25、465 或 587")
    EMAIL_HOST_USER: str = Field(description="发件人邮箱账号（用于身份认证）")
    EMAIL_HOST_PASSWORD: str = Field(description="授权码（网易邮箱设置中的应用专用密码）")
    EMAIL_USE_TLS: str = Field(description="是否使用 TLS（一般为 False，SSL 使用端口 465）")
    EMAIL_FROM: str = Field(description="显示在邮件中的发件人地址")
    WANGYI_EMAIL_TEMPLATE: dict = Field(default_factory=dict, description="网易邮箱模板配置")

    # ========== 媒体文件配置 ==========
    MEDIA_ROOT: str = Field(description="媒体文件根路径，存放用户上传内容")
    MEDIA_URL: str = Field(description="媒体文件访问URL前缀")

    # ========== 日志配置 ==========
    LOG_LEVEL: str = Field(description="日志级别，例如：INFO、DEBUG、WARNING")

    # ========== 配置类设置 ==========
    class Config:
        env_file = ".env"  # 指定默认 .env 文件路径
        case_sensitive = True  # 环境变量名称区分大小写

    # ========== 计算属性 ==========

    @property
    def DATABASE_URL(self) -> str:
        """拼接异步数据库连接地址"""
        return f"{self.ASYNC_DB_DRIVER}://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def SYNC_DATABASE_URL(self) -> str:
        """拼接同步数据库连接地址（用于 Alembic 迁移）"""
        return f"{self.SYNC_DB_DRIVER}://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def media_root_abs(self) -> str:
        """计算 MEDIA_ROOT 绝对路径，相对于 main.py 同级目录"""
        base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))  # app 目录
        project_root = os.path.abspath(os.path.join(base_dir, ".."))  # main.py 在上一级目录
        return os.path.abspath(os.path.join(project_root, self.MEDIA_ROOT))

    @property
    def media_root_parent(self) -> str:
        """获取 media_root_abs 的上一级目录"""
        return os.path.dirname(self.media_root_abs)

    @property
    def MONGODB_URL(self) -> str:
        """
        拼接 MongoDB 连接地址：
        - 有用户名和密码时：mongodb://user:pass@host:port/auth_db
        - 无用户名或密码时：mongodb://host:port/auth_db
        """
        user = (self.MONGODB_USER or "").strip()
        pwd = (self.MONGODB_PASSWORD or "").strip()
        if user and pwd:
            return f"mongodb://{user}:{pwd}@{self.MONGODB_HOST}:{self.MONGODB_PORT}/{self.MONGODB_AUTH_SOURCE}"
        else:
            return f"mongodb://{self.MONGODB_HOST}:{self.MONGODB_PORT}/{self.MONGODB_AUTH_SOURCE}"

    @property
    def REDIS_URL(self) -> str:
        """
        拼接 Redis 连接地址：
        - 有密码时：redis://:password@host:port/0
        - 无密码或全是空格时：redis://host:port/0
        """
        pwd = (self.REDIS_PASSWORD or "").strip()
        if pwd:
            return f"redis://:{pwd}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"
        else:
            return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    # ========== 配置加载逻辑 ==========

    @classmethod
    def customise_sources(cls, init_settings, env_settings, file_secret_settings):
        from dotenv import dotenv_values

        # 只加载 .env 文件
        env_vars = dotenv_values(".env")

        # 自动解析 JSON 字符串到 dict（邮箱模板）
        try:
            env_vars["WANGYI_EMAIL_TEMPLATE"] = json.loads(env_vars.get("WANGYI_EMAIL_TEMPLATE", "{}"))
        except (json.JSONDecodeError, KeyError):
            env_vars["WANGYI_EMAIL_TEMPLATE"] = {}

        return env_settings, file_secret_settings, lambda _: env_vars


# 实例化配置对象，全局共享
settings = Settings()

# 修正：Config 里不能直接引用 Settings，需类定义后赋值
Settings.Config.customise_sources = Settings.customise_sources

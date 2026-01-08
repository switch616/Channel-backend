"""
应用配置文件
使用 pydantic-settings 管理配置

配置加载顺序：
1. 读取 .env 文件获取 APP_ENV（公共配置）
2. 根据 APP_ENV 读取对应的 .env.{env} 文件（环境特定配置）
3. 环境特定配置会覆盖公共配置
4. 系统环境变量优先级最高（可覆盖文件配置）

文件结构：
- .env: 公共配置，包含 APP_ENV 环境标识
- .env.dev: 开发环境特定配置
- .env.test: 测试环境特定配置
- .env.prod: 生产环境特定配置
"""

import os
import json
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    应用配置类
    """

    # ========= 数据库 =========
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    ASYNC_DB_DRIVER: str = "mysql+asyncmy"
    SYNC_DB_DRIVER: str = "mysql+mysqlconnector"

    # ========= Redis =========
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: str = ""

    # ========= MongoDB =========
    MONGODB_HOST: str
    MONGODB_PORT: int
    MONGODB_USER: str
    MONGODB_PASSWORD: str
    MONGODB_DB: str
    MONGODB_AUTH_SOURCE: str = "admin"

    # ========= JWT =========
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # ========= Email =========
    EMAIL_HOST: str
    EMAIL_PORT: int
    EMAIL_HOST_USER: str
    EMAIL_HOST_PASSWORD: str
    EMAIL_USE_TLS: bool
    EMAIL_FROM: str
    WANGYI_EMAIL_TEMPLATE: dict = Field(default_factory=dict)

    # ========= Media =========
    MEDIA_ROOT: str
    MEDIA_URL: str

    # ========= Log =========
    LOG_LEVEL: str

    # ========= Test Mode =========
    # 测试模式配置（仅在 APP_ENV=test 时生效）
    TEST_MODE_MAX_VIDEOS: int = Field(default=10, description="测试模式下每个用户最大视频上传数量")
    TEST_MODE_IP_WHITELIST: str = Field(default="", description="测试模式IP白名单，逗号分隔，留空则不限制")

    # ========= Config =========
    class Config:
        case_sensitive = True

    # ========= pydantic-settings v2 正确钩子 =========
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        from dotenv import dotenv_values

        # 1. 先读取公共 .env 文件获取 APP_ENV
        base_env_vars = dotenv_values(".env")
        # 优先使用系统环境变量，其次使用 .env 文件中的值
        env = os.getenv("APP_ENV") or base_env_vars.get("APP_ENV", "dev")
        
        # 2. 读取对应环境的配置文件
        env_file = f".env.{env}"
        env_vars = dotenv_values(env_file)
        
        # 3. 合并公共配置和环境特定配置（环境特定配置优先）
        # 先加载公共配置，再加载环境特定配置覆盖
        merged_vars = {**base_env_vars, **env_vars}
        
        # 4. 移除 APP_ENV，因为它只是用来决定加载哪个环境文件的，不是配置项
        merged_vars.pop("APP_ENV", None)

        # JSON 字段手动反序列化
        try:
            merged_vars["WANGYI_EMAIL_TEMPLATE"] = json.loads(
                merged_vars.get("WANGYI_EMAIL_TEMPLATE", "{}")
            )
        except Exception:
            merged_vars["WANGYI_EMAIL_TEMPLATE"] = {}

        def custom_dotenv_settings():
            return merged_vars

        # 顺序 = 优先级（前面的优先）
        return (
            init_settings,
            custom_dotenv_settings,  # .env + .env.{env}
            env_settings,            # 系统环境变量（可覆盖）
            file_secret_settings,
        )

    # ========= 计算属性 =========
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"{self.ASYNC_DB_DRIVER}://"
            f"{self.DB_USER}:{self.DB_PASSWORD}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def SYNC_DATABASE_URL(self) -> str:
        return (
            f"{self.SYNC_DB_DRIVER}://"
            f"{self.DB_USER}:{self.DB_PASSWORD}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def MONGODB_URL(self) -> str:
        if self.MONGODB_USER and self.MONGODB_PASSWORD:
            return (
                f"mongodb://{self.MONGODB_USER}:{self.MONGODB_PASSWORD}"
                f"@{self.MONGODB_HOST}:{self.MONGODB_PORT}/{self.MONGODB_AUTH_SOURCE}"
            )
        return f"mongodb://{self.MONGODB_HOST}:{self.MONGODB_PORT}/{self.MONGODB_AUTH_SOURCE}"

    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    @property
    def media_root_abs(self) -> str:
        """媒体文件根目录的绝对路径"""
        base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        project_root = os.path.abspath(os.path.join(base_dir, ".."))
        return os.path.join(project_root, self.MEDIA_ROOT)
    
    @property
    def media_root_parent(self) -> str:
        """媒体文件根目录的绝对路径（别名，保持向后兼容）"""
        return os.path.abspath(os.path.dirname(self.media_root_abs))


# ========= 全局唯一实例 =========
settings = Settings()

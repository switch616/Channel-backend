"""
应用配置文件
使用 pydantic-settings 管理配置
支持 APP_ENV=dev|test|prod + .env.dev/.env.test/.env.prod
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

        env = os.getenv("APP_ENV", "dev")
        env_file = f".env.{env}"

        env_vars = dotenv_values(env_file)

        # JSON 字段手动反序列化
        try:
            env_vars["WANGYI_EMAIL_TEMPLATE"] = json.loads(
                env_vars.get("WANGYI_EMAIL_TEMPLATE", "{}")
            )
        except Exception:
            env_vars["WANGYI_EMAIL_TEMPLATE"] = {}

        def custom_dotenv_settings():
            return env_vars

        # 顺序 = 优先级（前面的优先）
        return (
            init_settings,
            custom_dotenv_settings,  # .env.dev / .env.prod
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
        base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        project_root = os.path.abspath(os.path.join(base_dir, ".."))
        return os.path.join(project_root, self.MEDIA_ROOT)


# ========= 全局唯一实例 =========
settings = Settings()

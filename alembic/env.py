import os
from dotenv import load_dotenv, dotenv_values
from app.core.config import settings
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# 获取 Alembic 配置对象
config = context.config

# 如果指定了配置文件，则加载日志配置
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 1. 先读取公共 .env 文件获取 APP_ENV
base_env_vars = dotenv_values(".env")
# 优先使用系统环境变量，其次使用 .env 文件中的值
app_env = os.getenv("APP_ENV") or base_env_vars.get("APP_ENV", "dev")

# 2. 读取对应环境的配置文件
env_file = f".env.{app_env}"
load_dotenv(env_file)  # 加载环境特定配置

# 3. 也加载公共 .env（公共配置会被环境特定配置覆盖）
load_dotenv(".env", override=False)

# 替换 alembic 的 config
config.set_main_option("sqlalchemy.url", settings.SYNC_DATABASE_URL)

# 导入 Base 和所有模型，确保所有表都被注册到 metadata 中
# 注意：必须先导入 Base，然后导入所有模型文件
from app.models.mysql import Base

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    离线模式运行迁移（不使用数据库连接池）
    适用于命令行操作或无法直接连接数据库的环境
    """
    # 从配置中获取数据库连接URL
    url = config.get_main_option("sqlalchemy.url")
    
    # 配置迁移上下文
    context.configure(
        url=url,                     # 数据库连接URL
        target_metadata=target_metadata,  # SQLAlchemy 元数据对象
        literal_binds=True,          # 直接使用字面值绑定参数
        dialect_opts={"paramstyle": "named"},  # SQL参数风格
    )

    # 开始事务并运行迁移
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """
    在线模式运行迁移（使用数据库连接池）
    适用于常规的迁移操作
    """
    # 从配置创建数据库引擎
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),  # 获取配置节
        prefix="sqlalchemy.",        # 配置项前缀
        poolclass=pool.NullPool,     # 不使用连接池
    )

    # 获取数据库连接并运行迁移
    with connectable.connect() as connection:
        # 配置迁移上下文
        context.configure(
            connection=connection,      # 使用活动的数据库连接
            target_metadata=target_metadata  # SQLAlchemy 元数据对象
        )

        # 开始事务并运行迁移
        with context.begin_transaction():
            context.run_migrations()

# 根据运行模式选择离线或在线迁移
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

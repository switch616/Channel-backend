# 1. 清空 alembic_version
#TRUNCATE TABLE alembic_version;

# 2. 重新生成迁移
#alembic revision --autogenerate -m "rebuild migrations"

# 3. 升级
alembic upgrade head

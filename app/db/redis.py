import aioredis
from app.core.config import settings

# 创建 Redis 连接池
redis_client = None

async def get_redis_aioredis_client():
    global redis_client
    if not redis_client:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding='utf-8',
            decode_responses=True
        )
    return redis_client

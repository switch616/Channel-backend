# test/test_redis.py
from test.base import BaseTestCase, settings
from app.db.redis import get_redis_aioredis_client

class TestRedis(BaseTestCase):

    async def test_redis_connection(self):
        client = await get_redis_aioredis_client()
        self.assertIsNotNone(client)
        print("Redis connection test passed.")

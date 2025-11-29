from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class MongoDB:
    client: AsyncIOMotorClient = None
    db = None


mongodb = MongoDB()


async def connect_to_mongo():
    """连接到MongoDB"""
    try:
        mongodb.client = AsyncIOMotorClient(settings.MONGODB_URL)
        # 测试连接
        await mongodb.client.admin.command('ping')
        mongodb.db = mongodb.client[settings.MONGODB_DB]
        logger.info("Connected to MongoDB successfully.")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def close_mongo_connection():
    """关闭MongoDB连接"""
    if mongodb.client:
        mongodb.client.close()
        logger.info("Disconnected from MongoDB.")


def get_mongo_db():
    """获取MongoDB数据库实例"""
    return mongodb.db 
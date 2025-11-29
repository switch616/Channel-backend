# test/test_mongodb.py
from test.base import BaseTestCase, settings
from app.db.mongdb import connect_to_mongo, get_mongo_db

class TestMongoDB(BaseTestCase):

    async def test_connect(self):
        await connect_to_mongo()
        db = get_mongo_db()
        self.assertIsNotNone(db)

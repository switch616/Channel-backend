# test/test_mysql.py
from test.base import BaseTestCase, settings
from app.db.mysql import get_db
import asyncio

class TestMySQL(BaseTestCase):

    async def test_mysql_session(self):
        async for session in get_db():
            self.assertIsNotNone(session)
            print("MySQL session test passed.")

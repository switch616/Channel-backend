# test/base.py
import os
import sys
import unittest

# 自动把项目根目录加入 PYTHONPATH
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.core.config import settings

import unittest
import asyncio


class BaseTestCase(unittest.IsolatedAsyncioTestCase):

    # 异步类级别 setup/teardown
    @classmethod
    async def asyncSetUpClass(cls):
        print("=== async init class ===")

    @classmethod
    async def asyncTearDownClass(cls):
        print("=== async teardown class ===")

    # 同步每个方法 setup/teardown
    def setUp(self):
        print("=== sync setup ===")

    def tearDown(self):
        print("=== sync teardown ===")

    # 异步每个方法 setup/teardown
    async def asyncSetUp(self):
        print("=== async setup ===")

    async def asyncTearDown(self):
        print("=== async teardown ===")

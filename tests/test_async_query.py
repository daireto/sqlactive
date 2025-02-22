import asyncio
import unittest

from sqlactive.async_query import AsyncQuery
from sqlactive.conn import DBConnection

from ._logger import logger
from ._models import BaseModel, Post, User
from ._seed import Seed


class TestAsyncQuery(unittest.IsolatedAsyncioTestCase):
    """Tests for ``sqlactive.async_query.AsyncQuery``."""

    DB_URL = 'sqlite+aiosqlite://'

    @classmethod
    def setUpClass(cls):
        logger.info('***** AsyncQuery tests *****')
        logger.info('Creating DB connection...')
        cls.conn = DBConnection(cls.DB_URL, echo=False)
        seed = Seed(cls.conn, BaseModel)
        asyncio.run(seed.run())

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'conn'):
            logger.info('Closing DB connection...')
            asyncio.run(cls.conn.close(BaseModel))

    async def test_init(self):
        """Test for ``fill`` function."""
        logger.info('Testing constructor...')
        async_query = AsyncQuery(User.query)
        users = await async_query.all()
        self.assertEqual(34, len(users))

    async def test_query(self):
        """Test for ``fill`` function."""
        logger.info('Testing "query" property...')
        async_query = User.get_async_query()
        async_query.query = async_query.query.limit(1)
        users = (await async_query.execute()).scalars().all()
        self.assertEqual(1, len(users))
        self.assertEqual('Bob Williams', users[0].name)

    async def test_str_and_repr(self):
        """Test for ``__str__`` and ``__repr__`` functions."""
        logger.info('Testing "__str__" and "__repr__" functions...')
        async_query = User.get_async_query()
        self.assertEqual(repr(async_query), str(async_query.query))
        self.assertEqual(str(async_query), str(async_query.query))

    async def test_filter_and_find(self):
        """Test for ``filter`` and ``find`` functions."""
        logger.info('Testing "filter" and "find" functions...')
        async_query = User.get_async_query()
        user = await async_query.filter(username='Joe156').one()
        self.assertEqual('Joe Smith', user.name)
        user = await async_query.find(username='Joe156').one()
        self.assertEqual('Joe Smith', user.name)

    async def test_sort(self):
        """Test for ``sort`` function."""
        logger.info('Testing "sort" function...')
        async_query = User.get_async_query()
        users = await async_query.filter(username__like='Ji%').all()
        self.assertEqual('Jim32', users[0].username)
        users = (
            await async_query.sort(User.username)
            .filter(username__like='Ji%')
            .all()
        )
        self.assertEqual('Jill874', users[0].username)
        async_query = Post.get_async_query()
        posts = await async_query.sort('-rating', 'user___name').all()
        self.assertEqual(24, len(posts))

    async def test_skip(self):
        """Test for ``skip`` function."""
        logger.info('Testing "skip" function...')
        async_query = User.get_async_query()
        users = await async_query.skip(1).filter(username__like='Ji%').all()
        self.assertEqual(2, len(users))
        users = await async_query.skip(2).filter(username__like='Ji%').all()
        self.assertEqual(1, len(users))

    async def test_take_and_top(self):
        """Test for ``take`` and ``top`` functions."""
        logger.info('Test for "take" and "top" functions...')
        async_query = User.get_async_query()
        users = await async_query.take(2).filter(username__like='Ji%').all()
        self.assertEqual(2, len(users))
        users = await async_query.top(1).filter(username__like='Ji%').all()
        self.assertEqual(1, len(users))

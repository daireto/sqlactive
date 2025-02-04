import asyncio
import unittest

from sqlactive.async_query import AsyncQuery
from sqlactive.conn import DBConnection
from sqlactive.exceptions import NoSessionError

from ._logger import logger
from ._models import BaseModel, User, Post
from ._seed import Seed


class TestAsyncQuery(unittest.IsolatedAsyncioTestCase):
    """Tests for `sqlactive.async_query.AsyncQuery`."""

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
        """Test for `fill` function."""

        logger.info('Testing constructor...')
        async_query = AsyncQuery(User._query)
        with self.assertRaises(NoSessionError) as context:
            await async_query.execute()
        self.assertEqual('Cannot get session. Please, call self.set_session()', str(context.exception))
        async_query.set_session(User._AsyncSession)
        users = await async_query.all()
        self.assertEqual(34, len(users))

    async def test_query(self):
        """Test for `fill` function."""

        logger.info('Testing `query` property...')
        async_query = User._get_async_query()
        async_query.query = async_query.query.limit(1)
        users = (await async_query.execute()).scalars().all()
        self.assertEqual(1, len(users))
        self.assertEqual('Bob Williams', users[0].name)

    async def test_str(self):
        """Test for `__str__` function."""

        logger.info('Testing `__str__` function...')
        async_query = User._get_async_query()
        self.assertEqual(str(async_query), str(async_query.query))

    async def test_filter(self):
        """Test for `filter` and `find` functions."""

        logger.info('Testing `filter` and `find` functions...')
        async_query = User._get_async_query()
        user = await async_query.filter(username='Joe156').one()
        self.assertEqual('Joe Smith', user.name)
        user = await async_query.find(username='Joe156').one()
        self.assertEqual('Joe Smith', user.name)

    async def test_sort(self):
        """Test for `sort` function."""

        logger.info('Testing `sort` function...')
        async_query = User._get_async_query()
        users = await async_query.filter(username__like='Ji%').all()
        self.assertEqual('Jim32', users[0].username)
        users = await async_query.sort(User.username).filter(username__like='Ji%').all()
        self.assertEqual('Jill874', users[0].username)
        async_query = Post._get_async_query()
        posts = await async_query.sort('-rating', 'user___name').all()
        self.assertEqual(24, len(posts))

    async def test_skip(self):
        """Test for `skip` function."""

        logger.info('Testing `skip` function...')
        async_query = User._get_async_query()
        users = await async_query.skip(1).filter(username__like='Ji%').all()
        self.assertEqual(2, len(users))
        users = await async_query.skip(2).filter(username__like='Ji%').all()
        self.assertEqual(1, len(users))

    async def test_limit(self):
        """Test for `take` function."""

        logger.info('Test for `take` function...')
        async_query = User._get_async_query()
        users = await async_query.take(2).filter(username__like='Ji%').all()
        self.assertEqual(2, len(users))
        users = await async_query.take(1).filter(username__like='Ji%').all()
        self.assertEqual(1, len(users))

import asyncio
import unittest

from sqlalchemy.sql import asc, desc
from sqlalchemy.sql.operators import like_op
from sqlalchemy.orm import joinedload, subqueryload, selectinload

from sqlactive import JOINED, SUBQUERY, SELECT_IN
from sqlactive.conn import DBConnection

from ._logger import logger
from ._models import User, Comment
from ._seed import Seed


class TestSmartQueryMixin(unittest.IsolatedAsyncioTestCase):
    """Tests for `sqlactive.smart_query.SmartQueryMixin`."""

    DB_URL = 'sqlite+aiosqlite://'

    @classmethod
    def setUpClass(cls):
        logger.info('SmartQueryMixin tests...')
        logger.info('Creating DB connection...')
        cls.conn = DBConnection(cls.DB_URL, echo=False)
        seed = Seed(cls.conn)
        asyncio.run(seed.run())

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'conn'):
            logger.info('Closing DB connection...')
            asyncio.run(cls.conn.close())

    async def test_filter_expr(self):
        """Test for `filter_expr` function."""

        logger.info('Testing `filter_expr` function...')
        expressions = User.filter_expr(username__like='Ji%', age__in=[30, 32, 34])
        expected_expressions = [like_op(User.username, 'Ji%'), User.age.in_([30, 32, 34])]
        users = [user.username for user in await User.find(*expressions).all()]
        expected_users = [user.username for user in await User.find(*expected_expressions).all()]
        self.assertCountEqual(expected_users, users)
        self.assertEqual('Jill874', users[0])

    async def test_order_expr(self):
        """Test for `order_expr` function."""

        logger.info('Testing `order_expr` function...')
        expressions = User.order_expr('-age', 'username')
        expected_expressions = [desc(User.age), asc(User.username)]
        users = [user.username for user in await User.sort(*expressions).all()]
        expected_users = [user.username for user in await User.sort(*expected_expressions).all()]
        self.assertCountEqual(expected_users, users)
        self.assertEqual('Bill65', users[0])
        self.assertEqual('John84', users[-1])

    async def test_eager_expr(self):
        """Test for `eager_expr` function."""

        logger.info('Testing `eager_expr` function...')
        schema = {
            User.posts: JOINED,
            User.comments: (SUBQUERY, {Comment.post: SELECT_IN}),
        }
        expressions = User.eager_expr(schema)
        expected_expressions = [
            joinedload(User.posts),
            subqueryload(User.comments).options(selectinload(Comment.post)),
        ]
        users = [user.to_dict(nested=True) for user in await User.options(*expressions).unique_all()]
        expected_users = [user.to_dict(nested=True) for user in await User.options(*expected_expressions).unique_all()]
        self.assertEqual(expected_users, users)
        self.assertEqual('Bob28', users[0]['username'])
        self.assertEqual(4, users[0]['posts'][0]['rating'])
        self.assertEqual('Bob28', expected_users[0]['username'])
        self.assertEqual(4, expected_users[0]['posts'][0]['rating'])

import asyncio
import unittest

from sqlactive.conn import DBConnection

from ._logger import logger
from ._models import User
from ._seed import Seed


class TestBaseModel(unittest.IsolatedAsyncioTestCase):
    """Tests for `sqlactive.base_model.ActiveRecordBaseModel`."""

    DB_URL = 'sqlite+aiosqlite://'

    @classmethod
    def setUpClass(cls):
        logger.info('ActiveRecordBaseModel tests...')
        logger.info('Creating DB connection...')
        cls.conn = DBConnection(cls.DB_URL, echo=False)
        seed = Seed(cls.conn)
        asyncio.run(seed.run())

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'conn'):
            logger.info('Closing DB connection...')
            asyncio.run(cls.conn.close())

    async def test_repr(self):
        """Test for `__repr__` function."""

        logger.info('Testing `__repr__` function...')
        user = await User.get_or_fail(1)
        self.assertEqual('<User #1>', str(user))

    async def test_to_dict(self):
        """Test for `to_dict` function."""

        logger.info('Testing `to_dict` function...')
        user = await User.with_subquery(User.posts).filter(id=1).one()
        self.assertDictEqual(
            {
                'id': user.id,
                'username': user.username,
                'name': user.name,
                'age': user.age,
                'created_at': user.created_at,
                'updated_at': user.updated_at,
            },
            user.to_dict(),
        )
        self.assertDictEqual(
            {
                'id': user.id,
                'username': user.username,
                'name': user.name,
                'age': user.age,
                'created_at': user.created_at,
                'updated_at': user.updated_at,
                'is_adult': user.is_adult,
            },
            user.to_dict(hybrid_attributes=True),
        )
        self.assertDictEqual(
            {
                'id': user.id,
                'username': user.username,
                'name': user.name,
                'age': user.age,
                'is_adult': user.is_adult,
            },
            user.to_dict(hybrid_attributes=True, exclude=['created_at', 'updated_at']),
        )
        self.assertDictEqual(
            {
                'id': user.id,
                'username': user.username,
                'name': user.name,
                'age': user.age,
                'posts': [post.to_dict() for post in user.posts],
                'is_adult': user.is_adult,
            },
            user.to_dict(nested=True, hybrid_attributes=True, exclude=['created_at', 'updated_at']),
        )

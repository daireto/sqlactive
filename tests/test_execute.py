import asyncio
import unittest

from sqlalchemy.sql import func, select

from sqlactive.base_model import ActiveRecordBaseModel
from sqlactive.conn import DBConnection, execute
from sqlactive.exceptions import NoSessionError

from ._logger import logger
from ._models import BaseModel, User
from ._seed import Seed


class TestExecuteFunction(unittest.IsolatedAsyncioTestCase):
    """Tests for ``sqlactive.conn.execute`` function."""

    DB_URL = 'sqlite+aiosqlite://'

    @classmethod
    def setUpClass(cls):
        logger.info('***** "execute" tests *****')
        logger.info('Creating DB connection...')
        cls.conn = DBConnection(cls.DB_URL, echo=False)
        seed = Seed(cls.conn, BaseModel)
        asyncio.run(seed.run())

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'conn'):
            logger.info('Closing DB connection...')
            asyncio.run(cls.conn.close())

    async def test_execute(self):
        """Test for ``sqlactive.conn.execute`` function."""
        logger.info('Testing "execute" function...')
        query = select(User.age, func.count(User.id)).group_by(User.age)
        result = await execute(self.conn.async_scoped_session, query)
        self.assertEqual((19, 1), next(result))
        self.assertEqual((24, 1), next(result))
        self.assertEqual((25, 2), next(result))
        self.assertEqual((26, 2), next(result))
        self.assertEqual((27, 3), next(result))

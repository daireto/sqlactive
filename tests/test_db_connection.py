import unittest

from sqlactive.base_model import ActiveRecordBaseModel
from sqlactive.conn import DBConnection

from ._logger import logger
from ._models import BaseModel


class TestDBConnection(unittest.IsolatedAsyncioTestCase):
    """Tests for ``sqlactive.conn.DBConnection`` class."""

    DB_URL = 'sqlite+aiosqlite://'

    async def test_all(self):
        """Test for ``init_db`` function."""
        logger.info('Testing constructor...')
        conn = DBConnection(self.DB_URL, echo=False)

        logger.info('Testing "init_db" function...')
        await conn.init_db()
        await conn.init_db(BaseModel)
        self.assertIsNotNone(ActiveRecordBaseModel._session)
        self.assertIsNotNone(BaseModel._session)

        logger.info('Testing "close" function...')
        await conn.close(BaseModel)

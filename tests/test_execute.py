import unittest

from sqlalchemy.sql import select, func

from sqlactive.conn import DBConnection, execute
from sqlactive.exceptions import NoSessionError

from ._logger import logger
from ._models import BaseModel, User
from ._seed import Seed


class TestExecuteFunction(unittest.IsolatedAsyncioTestCase):
    """Tests for `sqlactive.conn.execute` function."""

    DB_URL = 'sqlite+aiosqlite://'

    async def test_execute_with_base_model(self):
        """Tests for `sqlactive.conn.execute` function
        using a `BaseModel` class.
        """

        logger.info('Testing with BaseModel...')
        conn = DBConnection(self.DB_URL, echo=False)
        seed = Seed(conn, BaseModel)
        await seed.run()
        query = select(User.age, func.count(User.id)).group_by(User.age)
        result = await execute(query, BaseModel)
        self.assertEqual((19, 1), next(result))
        self.assertEqual((24, 1), next(result))
        self.assertEqual((25, 2), next(result))
        self.assertEqual((26, 2), next(result))
        self.assertEqual((27, 3), next(result))
        with self.assertRaises(NoSessionError):
            query = select(User.age, func.count(User.id)).group_by(User.age)
            await execute(query)
        await conn.close(BaseModel)

    async def test_execute_with_active_record_base_model(self):
        """Tests for `sqlactive.conn.execute` function
        using the `ActiveRecordBaseModel` class.
        """

        logger.info('Testing with ActiveRecordBaseModel...')
        conn = DBConnection(self.DB_URL, echo=False)
        seed = Seed(conn)
        await seed.run()
        query = select(User.age, func.count(User.id)).group_by(User.age)
        result = await execute(query)
        self.assertEqual((19, 1), next(result))
        self.assertEqual((24, 1), next(result))
        self.assertEqual((25, 2), next(result))
        self.assertEqual((26, 2), next(result))
        self.assertEqual((27, 3), next(result))
        await conn.close()

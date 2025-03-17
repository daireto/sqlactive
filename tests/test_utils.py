import asyncio
import unittest

from sqlalchemy.sql import func, select
from sqlalchemy.sql.operators import and_, or_

from sqlactive import JOINED, SELECT_IN, SUBQUERY
from sqlactive.conn import DBConnection
from sqlactive.utils import (
    eager_expr_from_schema,
    flatten_nested_filter_keys,
    get_query_root_cls,
)

from ._logger import logger
from ._models import BaseModel, Comment, Post
from ._seed import Seed


class TestSmartQueryMixin(unittest.IsolatedAsyncioTestCase):
    """Tests for ``sqlactive.smart_query.SmartQueryMixin``."""

    DB_URL = 'sqlite+aiosqlite://'

    @classmethod
    def setUpClass(cls):
        logger.info('***** SmartQueryMixin tests *****')
        logger.info('Creating DB connection...')
        cls.conn = DBConnection(cls.DB_URL, echo=False)
        seed = Seed(cls.conn, BaseModel)
        asyncio.run(seed.run())

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'conn'):
            logger.info('Closing DB connection...')
            asyncio.run(cls.conn.close(BaseModel))

    def test_get_query_root_cls(self):
        """Test for ``get_query_root_cls`` function."""
        logger.info('Testing "get_query_root_cls" function...')
        query = Post.query
        self.assertEqual(Post, get_query_root_cls(query))
        query = Post.query.join(Comment)
        self.assertEqual(Post, get_query_root_cls(query))
        query = select(Post.id)
        self.assertEqual(Post, get_query_root_cls(query))
        query = select(Post.id, Comment.id)
        self.assertEqual(Post, get_query_root_cls(query))
        query = select(func.count(Post.id))
        self.assertEqual(Post, get_query_root_cls(query))
        query = select(func.count('*'))
        self.assertIsNone(get_query_root_cls(query))
        query = select(func.count('*'))
        with self.assertRaises(ValueError):
            get_query_root_cls(query, raise_on_none=True)

    def test_flatten_filter_keys(self):
        """Test for ``flatten_filter_keys`` function."""
        logger.info('Testing "flatten_filter_keys" function...')
        filter_keys = list(
            flatten_nested_filter_keys(
                {
                    or_: {
                        'id__gt': 1000,
                        and_: {
                            'id__lt': 500,
                            'related___property__in': (1, 2, 3),
                        },
                    }
                }
            )
        )
        self.assertCountEqual(
            ['id__gt', 'id__lt', 'related___property__in'], filter_keys
        )
        filter_keys = list(
            flatten_nested_filter_keys(
                [{'id__lt': 500}, {'related___property__in': (1, 2, 3)}]
            )
        )
        self.assertCountEqual(
            ['id__lt', 'related___property__in'], filter_keys
        )
        with self.assertRaises(TypeError):
            filter_keys = list(
                flatten_nested_filter_keys({or_: {'id__gt': 1000}, and_: True})
            )

    async def test_eager_expr_from_schema(self):
        """Test for ``eager_expr_from_schema`` function."""
        logger.info('Testing "eager_expr_from_schema" function...')
        schema = {
            Post.user: JOINED,
            Post.comments: (SUBQUERY, {Comment.user: SELECT_IN}),
        }
        eager_expr = eager_expr_from_schema(schema)
        post1 = await Post.options(*eager_expr).limit(1).unique_one()
        self.assertEqual('Bob Williams', post1.user.name)
        self.assertEqual('Bob Williams', post1.comments[0].user.name)

        schema = {Post.user: JOINED, Post.comments: {Comment.user: SELECT_IN}}
        eager_expr = eager_expr_from_schema(schema)
        post2 = await Post.options(*eager_expr).limit(1).unique_one()
        self.assertEqual('Bob Williams', post2.user.name)
        self.assertEqual('Bob Williams', post2.comments[0].user.name)

        with self.assertRaises(ValueError):
            schema = {
                Post.user: JOINED,
                Post.comments: (SUBQUERY, {Comment.user: 'UNKNOWN'}),
            }
            eager_expr_from_schema(schema)

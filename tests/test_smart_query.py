import asyncio
import unittest

from collections import OrderedDict

from sqlalchemy.sql import asc, desc
from sqlalchemy.sql.operators import like_op, and_, or_
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import aliased, joinedload, subqueryload, selectinload

from sqlactive import JOINED, SUBQUERY, SELECT_IN
from sqlactive.smart_query import SmartQueryMixin
from sqlactive.conn import DBConnection

from ._logger import logger
from ._models import BaseModel, Post, User, Comment
from ._seed import Seed


class TestSmartQueryMixin(unittest.IsolatedAsyncioTestCase):
    """Tests for `sqlactive.smart_query.SmartQueryMixin`."""

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

    async def test_filter_expr(self):
        """Test for `filter_expr` function."""

        logger.info('Testing `filter_expr` function...')
        expressions = User.filter_expr(username__like='Ji%', age__in=[30, 32, 34])
        expected_expressions = [like_op(User.username, 'Ji%'), User.age.in_([30, 32, 34])]
        users = [user.username for user in await User.find(*expressions).all()]
        expected_users = [user.username for user in await User.find(*expected_expressions).all()]
        self.assertCountEqual(expected_users, users)
        self.assertEqual('Jill874', users[0])
        expressions = User.filter_expr(older_than=User(age=30))
        users = [user.username for user in await User.find(*expressions).all()]
        self.assertCountEqual(
            [
                'Bill65',
                'Jenny654',
                'Jim32',
                'Jill874',
                'Helen12',
                'Jack321',
                'Ian48',
                'Tom897',
                'Brad654',
                'Angel8499',
                'Bruce984',
                'Jennifer5215',
            ],
            users,
        )
        with self.assertRaises(KeyError) as context:
            User.filter_expr(username__unknown='Ji%')
        self.assertIn('`unknown`', str(context.exception))

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

    def test_flatten_filter_keys(self):
        """Test for `_flatten_filter_keys` function."""

        logger.info('Testing `_flatten_filter_keys` function...')
        filter_keys = list(
            SmartQueryMixin._flatten_filter_keys(
                {or_: {'id__gt': 1000, and_: {'id__lt': 500, 'related___property__in': (1, 2, 3)}}}
            )
        )
        self.assertCountEqual(['id__gt', 'id__lt', 'related___property__in'], filter_keys)
        filter_keys = list(
            SmartQueryMixin._flatten_filter_keys([{'id__lt': 500}, {'related___property__in': (1, 2, 3)}])
        )
        self.assertCountEqual(['id__lt', 'related___property__in'], filter_keys)
        with self.assertRaises(TypeError) as context:
            filter_keys = list(SmartQueryMixin._flatten_filter_keys({or_: {'id__gt': 1000}, and_: True}))
        self.assertIn('bool', str(context.exception))

    def test_parse_path_and_make_aliases(self):
        """Test for `_parse_path_and_make_aliases` function."""

        logger.info('Testing `_parse_path_and_make_aliases` function...')
        aliases = OrderedDict()
        SmartQueryMixin._parse_path_and_make_aliases(
            entity=Comment,
            entity_path='',
            attrs=['post___title', 'post___body', 'user___name', 'post_id', 'user_id', 'id'],
            aliases=aliases,
        )
        self.assertTrue(type(aliases['post'][0]) is type(aliased(Post)))
        self.assertTrue(inspect(aliases['post'][0]).mapper.class_ == Post)
        with self.assertRaises(KeyError) as context:
            SmartQueryMixin._parse_path_and_make_aliases(
                entity=Comment, entity_path='', attrs=['author___name', 'post_id', 'user_id', 'id'], aliases=aliases
            )
        self.assertIn('`author`', str(context.exception))

    def test_recurse_filters(self):
        """Test for `_recurse_filters` function."""

        logger.info('Testing `_recurse_filters` function...')
        aliases = OrderedDict(
            {
                'user': (aliased(Comment.user.property.mapper.class_), Comment.user),
                'post': (aliased(Comment.post.property.mapper.class_), Comment.post),
            }
        )
        filters = {or_: {'post___rating__gt': 3, and_: {'user___age__lt': 30, 'body__like': r'%elit.'}}}
        filters = SmartQueryMixin._recurse_filters(filters, root_cls=Comment, aliases=aliases)
        self.assertEqual(
            'posts_1.rating > :rating_1 OR users_1.age < :age_1 AND comments.body LIKE :body_1', str(next(filters))
        )
        filters = [{'user___age__lt': 30}, {'body__like': r'%elit.'}]
        filters = SmartQueryMixin._recurse_filters(filters, root_cls=Comment, aliases=aliases)
        self.assertEqual('users_1.age < :age_1', str(next(filters)))
        self.assertEqual('comments.body LIKE :body_1', str(next(filters)))
        with self.assertRaises(KeyError) as context:
            filters = {or_: {'post___score__gt': 3, and_: {'user___age__lt': 30, 'body__like': r'%elit.'}}}
            next(SmartQueryMixin._recurse_filters(filters, root_cls=Comment, aliases=aliases))
        self.assertIn('`post___score__gt`', str(context.exception))

    def test_sort_query(self):
        """Test for `_sort_query` function."""

        logger.info('Testing `_sort_query` function...')
        aliases = OrderedDict(
            {
                'user': (aliased(Post.user.property.mapper.class_), Post.user),
            }
        )
        sort_attrs = ['-created_at', 'user___name', '-user___age']
        query = SmartQueryMixin._sort_query(query=Post._query, sort_attrs=sort_attrs, root_cls=Post, aliases=aliases)
        self.assertTrue(str(query).endswith('posts.created_at DESC, users_1.name ASC, users_1.age DESC'))
        with self.assertRaises(KeyError) as context:
            SmartQueryMixin._sort_query(
                query=Post._query, sort_attrs=['-created_at', 'user___fullname'], root_cls=Post, aliases=aliases
            )
        self.assertIn('`user___fullname`', str(context.exception))

    async def test_eager_expr_from_schema(self):
        """Test for `_eager_expr_from_schema` function."""

        logger.info('Testing `_eager_expr_from_schema` function...')
        schema = {Post.user: JOINED, Post.comments: (SUBQUERY, {Comment.user: SELECT_IN})}
        eager_expr = SmartQueryMixin._eager_expr_from_schema(schema)
        post1 = await Post.options(*eager_expr).limit(1).unique_one()
        self.assertEqual('Bob Williams', post1.user.name)
        self.assertEqual('Bob Williams', post1.comments[0].user.name)

        schema = {Post.user: JOINED, Post.comments: {Comment.user: SELECT_IN}}
        eager_expr = SmartQueryMixin._eager_expr_from_schema(schema)
        post2 = await Post.options(*eager_expr).limit(1).unique_one()
        self.assertEqual('Bob Williams', post2.user.name)
        self.assertEqual('Bob Williams', post2.comments[0].user.name)

        with self.assertRaises(ValueError) as context:
            schema = {Post.user: JOINED, Post.comments: (SUBQUERY, {Comment.user: 'UNKNOWN'})}
            SmartQueryMixin._eager_expr_from_schema(schema)
        self.assertIn('`UNKNOWN`', str(context.exception))

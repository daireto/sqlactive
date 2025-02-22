import asyncio
import unittest
from collections import OrderedDict
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import aliased, joinedload, selectinload, subqueryload
from sqlalchemy.sql import asc, desc
from sqlalchemy.sql.operators import and_, or_

from sqlactive import JOINED, SELECT_IN, SUBQUERY
from sqlactive.conn import DBConnection
from sqlactive.exceptions import (
    InvalidJoinMethodError,
    NoColumnOrHybridPropertyError,
    NoFilterableError,
    NoSortableError,
    OperatorError,
    RelationError,
)
from sqlactive.smart_query import SmartQueryMixin

from ._logger import logger
from ._models import BaseModel, Comment, Post, User
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

    async def test_operators(self):
        """Test for operators."""
        logger.info('Testing operators...')
        today = datetime.today()
        post_with_topic = Post(
            title='Lorem ipsum',
            body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
            rating=4,
            user_id=1,
            topic='Some topic',
        )
        post_without_topic = Post(
            title='Lorem ipsum',
            body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
            rating=4,
            user_id=1,
        )

        async with post_with_topic, post_without_topic:
            self.assertTrue(
                all(
                    [
                        post.topic is None
                        for post in await Post.where(topic__isnull=True).all()
                    ]
                )
            )
            self.assertTrue(
                all(
                    [
                        post.topic is not None
                        for post in await Post.where(topic__isnull=False).all()
                    ]
                )
            )

        self.assertTrue(
            all(
                [
                    user.age == 25
                    for user in await User.where(age__exact=25).all()
                ]
            )
        )
        self.assertTrue(
            all(
                [user.age == 25 for user in await User.where(age__eq=25).all()]
            )
        )
        self.assertTrue(
            all(
                [user.age != 25 for user in await User.where(age__ne=25).all()]
            )
        )
        self.assertTrue(
            all([user.age > 25 for user in await User.where(age__gt=25).all()])
        )
        self.assertTrue(
            all(
                [user.age >= 25 for user in await User.where(age__ge=25).all()]
            )
        )
        self.assertTrue(
            all([user.age < 25 for user in await User.where(age__lt=25).all()])
        )
        self.assertTrue(
            all(
                [user.age <= 25 for user in await User.where(age__le=25).all()]
            )
        )
        self.assertTrue(
            all(
                [
                    user.age == 20 or user.age == 30
                    for user in await User.where(age__in=[20, 30]).all()
                ]
            )
        )
        self.assertTrue(
            all(
                [
                    user.age != 20 and user.age != 30
                    for user in await User.where(age__notin=[20, 30]).all()
                ]
            )
        )
        self.assertTrue(
            all(
                [
                    user.age >= 20 and user.age <= 30
                    for user in await User.where(age__between=[20, 30]).all()
                ]
            )
        )
        self.assertTrue(
            all(
                [
                    user.username.startswith('Ji')
                    for user in await User.where(username__like='Ji%').all()
                ]
            )
        )
        self.assertTrue(
            all(
                [
                    user.username.startswith('Ji')
                    for user in await User.where(username__ilike='ji%').all()
                ]
            )
        )
        self.assertTrue(
            all(
                [
                    user.username.startswith('Ji')
                    for user in await User.where(
                        username__startswith='Ji'
                    ).all()
                ]
            )
        )
        self.assertTrue(
            all(
                [
                    user.username.startswith('Ji')
                    for user in await User.where(
                        username__istartswith='ji'
                    ).all()
                ]
            )
        )
        self.assertTrue(
            all(
                [
                    user.name.endswith('Anderson')
                    for user in await User.where(
                        name__endswith='Anderson'
                    ).all()
                ]
            )
        )
        self.assertTrue(
            all(
                [
                    user.name.endswith('Anderson')
                    for user in await User.where(
                        name__iendswith='anderson'
                    ).all()
                ]
            )
        )
        self.assertTrue(
            all(
                [
                    'wa' in user.name.lower()
                    for user in await User.where(name__contains='Wa').all()
                ]
            )
        )
        self.assertTrue(
            all(
                [
                    user.created_at.year == today.year
                    for user in await User.where(
                        created_at__year=today.year
                    ).all()
                ]
            )
        )
        self.assertTrue(
            all(
                [
                    user.created_at.year != (today.year - 1)
                    for user in await User.where(
                        created_at__year_ne=today.year
                    ).all()
                ]
            )
        )
        self.assertTrue(
            all(
                [
                    user.created_at.year > (today.year - 1)
                    for user in await User.where(
                        created_at__year_gt=today.year
                    ).all()
                ]
            )
        )
        self.assertTrue(
            all(
                [
                    user.created_at.year >= (today.year - 1)
                    for user in await User.where(
                        created_at__year_ge=today.year
                    ).all()
                ]
            )
        )
        self.assertTrue(
            all(
                [
                    user.created_at.year < (today.year + 1)
                    for user in await User.where(
                        created_at__year_lt=today.year
                    ).all()
                ]
            )
        )
        self.assertTrue(
            all(
                [
                    user.created_at.year <= (today.year + 1)
                    for user in await User.where(
                        created_at__year_le=today.year
                    ).all()
                ]
            )
        )
        self.assertTrue(
            all(
                [
                    user.created_at.month == today.month
                    for user in await User.where(
                        created_at__month=today.month
                    ).all()
                ]
            )
        )
        self.assertTrue(
            all(
                [
                    user.created_at.month != (today.month - 1)
                    for user in await User.where(
                        created_at__month_ne=today.month
                    ).all()
                ]
            )
        )
        self.assertTrue(
            all(
                [
                    user.created_at.month > (today.month - 1)
                    for user in await User.where(
                        created_at__month_gt=today.month
                    ).all()
                ]
            )
        )
        self.assertTrue(
            all(
                [
                    user.created_at.month >= (today.month - 1)
                    for user in await User.where(
                        created_at__month_ge=today.month
                    ).all()
                ]
            )
        )
        self.assertTrue(
            all(
                [
                    user.created_at.month < (today.month + 1)
                    for user in await User.where(
                        created_at__month_lt=today.month
                    ).all()
                ]
            )
        )
        self.assertTrue(
            all(
                [
                    user.created_at.month <= (today.month + 1)
                    for user in await User.where(
                        created_at__month_le=today.month
                    ).all()
                ]
            )
        )
        self.assertTrue(
            all(
                [
                    user.created_at.day == today.day
                    for user in await User.where(
                        created_at__day=today.day
                    ).all()
                ]
            )
        )
        self.assertTrue(
            all(
                [
                    user.created_at.day != (today.day - 1)
                    for user in await User.where(
                        created_at__day_ne=today.day
                    ).all()
                ]
            )
        )
        self.assertTrue(
            all(
                [
                    user.created_at.day > (today.day - 1)
                    for user in await User.where(
                        created_at__day_gt=today.day
                    ).all()
                ]
            )
        )
        self.assertTrue(
            all(
                [
                    user.created_at.day >= (today.day - 1)
                    for user in await User.where(
                        created_at__day_ge=today.day
                    ).all()
                ]
            )
        )
        self.assertTrue(
            all(
                [
                    user.created_at.day < (today.day + 1)
                    for user in await User.where(
                        created_at__day_lt=today.day
                    ).all()
                ]
            )
        )
        self.assertTrue(
            all(
                [
                    user.created_at.day <= (today.day + 1)
                    for user in await User.where(
                        created_at__day_le=today.day
                    ).all()
                ]
            )
        )

    async def test_filter_expr(self):
        """Test for ``filter_expr`` function."""
        logger.info('Testing "filter_expr" function...')
        expressions = User.filter_expr(
            username__like='Ji%', age__in=[30, 32, 34]
        )
        expected_expressions = [
            User.username.like('Ji%'),
            User.age.in_([30, 32, 34]),
        ]
        users = [user.username for user in await User.find(*expressions).all()]
        expected_users = [
            user.username
            for user in await User.find(*expected_expressions).all()
        ]
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
        with self.assertRaises(OperatorError):
            User.filter_expr(username__unknown='Ji%')

    async def test_order_expr(self):
        """Test for ``order_expr`` function."""
        logger.info('Testing "order_expr" function...')
        expressions = User.order_expr('-age', 'username')
        expected_expressions = [desc(User.age), asc(User.username)]
        users = [user.username for user in await User.sort(*expressions).all()]
        expected_users = [
            user.username
            for user in await User.sort(*expected_expressions).all()
        ]
        self.assertCountEqual(expected_users, users)
        self.assertEqual('Bill65', users[0])
        self.assertEqual('John84', users[-1])

    async def test_columns_expr(self):
        """Test for ``columns_expr`` function."""
        logger.info('Testing "columns_expr" function...')
        expressions = Post.columns_expr('rating', 'title')
        expected_expressions = [Post.rating, Post.title]
        post_ratings = [
            (post[0], post[1])
            for post in await Post.select(Post.rating, func.count(Post.title))
            .group_by(*expressions)
            .all(scalars=False)
        ]
        expected_post_ratings = [
            (post[0], post[1])
            for post in await Post.select(Post.rating, func.count(Post.title))
            .group_by(*expected_expressions)
            .all(scalars=False)
        ]
        self.assertCountEqual(expected_post_ratings, post_ratings)
        self.assertEqual(5, post_ratings[0][1])
        self.assertEqual(4, post_ratings[-1][1])

    async def test_eager_expr(self):
        """Test for ``eager_expr`` function."""
        logger.info('Testing "eager_expr" function...')
        schema = {
            User.posts: JOINED,
            User.comments: (SUBQUERY, {Comment.post: SELECT_IN}),
        }
        expressions = User.eager_expr(schema)
        expected_expressions = [
            joinedload(User.posts),
            subqueryload(User.comments).options(selectinload(Comment.post)),
        ]
        users = [
            user.to_dict(nested=True)
            for user in await User.options(*expressions).unique_all()
        ]
        expected_users = [
            user.to_dict(nested=True)
            for user in await User.options(*expected_expressions).unique_all()
        ]
        self.assertEqual(expected_users, users)
        self.assertEqual('Bob28', users[0]['username'])
        self.assertEqual(4, users[0]['posts'][0]['rating'])
        self.assertEqual('Bob28', expected_users[0]['username'])
        self.assertEqual(4, expected_users[0]['posts'][0]['rating'])

    def test_flatten_filter_keys(self):
        """Test for ``_flatten_filter_keys`` function."""
        logger.info('Testing "_flatten_filter_keys" function...')
        filter_keys = list(
            SmartQueryMixin._flatten_filter_keys(
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
            SmartQueryMixin._flatten_filter_keys(
                [{'id__lt': 500}, {'related___property__in': (1, 2, 3)}]
            )
        )
        self.assertCountEqual(
            ['id__lt', 'related___property__in'], filter_keys
        )
        with self.assertRaises(TypeError):
            filter_keys = list(
                SmartQueryMixin._flatten_filter_keys(
                    {or_: {'id__gt': 1000}, and_: True}
                )
            )

    def test_make_aliases_from_attrs(self):
        """Test for ``_make_aliases_from_attrs`` function."""
        logger.info('Testing "_make_aliases_from_attrs" function...')
        aliases = OrderedDict()
        SmartQueryMixin._make_aliases_from_attrs(
            entity=Comment,
            entity_path='',
            attrs=[
                'post___title',
                'post___body',
                'user___name',
                'post_id',
                'user_id',
                'id',
            ],
            aliases=aliases,
        )
        self.assertTrue(type(aliases['post'][0]) is type(aliased(Post)))
        self.assertTrue(aliases['post'][0].__mapper__.class_ == Post)
        with self.assertRaises(RelationError):
            SmartQueryMixin._make_aliases_from_attrs(
                entity=Comment,
                entity_path='',
                attrs=['author___name', 'post_id', 'user_id', 'id'],
                aliases=aliases,
            )

    def test_recurse_filters(self):
        """Test for ``_recurse_filters`` function."""
        logger.info('Testing "_recurse_filters" function...')
        aliases = OrderedDict(
            {
                'user': (
                    aliased(Comment.user.property.mapper.class_),
                    Comment.user,
                ),
                'post': (
                    aliased(Comment.post.property.mapper.class_),
                    Comment.post,
                ),
            }
        )
        filters = {
            or_: {
                'post___rating__gt': 3,
                and_: {'user___age__lt': 30, 'body__like': r'%elit.'},
            }
        }
        filters = SmartQueryMixin._recurse_filters(
            filters, root_cls=Comment, aliases=aliases
        )
        self.assertEqual(
            'posts_1.rating > :rating_1 OR users_1.age < :age_1 AND comments.body LIKE :body_1',
            str(next(filters)),
        )
        filters = [{'user___age__lt': 30}, {'body__like': r'%elit.'}]
        filters = SmartQueryMixin._recurse_filters(
            filters, root_cls=Comment, aliases=aliases
        )
        self.assertEqual('users_1.age < :age_1', str(next(filters)))
        self.assertEqual('comments.body LIKE :body_1', str(next(filters)))
        with self.assertRaises(NoFilterableError):
            filters = {
                or_: {
                    'post___score__gt': 3,
                    and_: {'user___age__lt': 30, 'body__like': r'%elit.'},
                }
            }
            next(
                SmartQueryMixin._recurse_filters(
                    filters, root_cls=Comment, aliases=aliases
                )
            )

    def test_sort_query(self):
        """Test for ``_sort_query`` function."""
        logger.info('Testing "_sort_query" function...')
        aliases = OrderedDict(
            {
                'user': (aliased(Post.user.property.mapper.class_), Post.user),
            }
        )
        sort_attrs = ['-created_at', 'user___name', '-user___age']
        query = SmartQueryMixin._sort_query(
            query=Post.query,
            sort_attrs=sort_attrs,
            root_cls=Post,
            aliases=aliases,
        )
        self.assertTrue(
            str(query).endswith(
                'posts.created_at DESC, users_1.name ASC, users_1.age DESC'
            )
        )
        with self.assertRaises(NoSortableError):
            SmartQueryMixin._sort_query(
                query=Post.query,
                sort_attrs=['-created_at', 'user___fullname'],
                root_cls=Post,
                aliases=aliases,
            )

    def test_group_query(self):
        """Test for ``_group_query`` function."""
        logger.info('Testing "_group_query" function...')
        aliases = OrderedDict(
            {
                'user': (aliased(Post.user.property.mapper.class_), Post.user),
            }
        )
        group_attrs = ['rating', 'user___name']
        query = SmartQueryMixin._group_query(
            query=Post.query,
            group_attrs=group_attrs,
            root_cls=Post,
            aliases=aliases,
        )
        self.assertTrue(
            str(query).endswith('GROUP BY posts.rating, users_1.name')
        )
        with self.assertRaises(NoColumnOrHybridPropertyError):
            SmartQueryMixin._group_query(
                query=Post.query,
                group_attrs=['rating', 'user___fullname'],
                root_cls=Post,
                aliases=aliases,
            )

    async def test_eager_expr_from_schema(self):
        """Test for ``_eager_expr_from_schema`` function."""
        logger.info('Testing "_eager_expr_from_schema" function...')
        schema = {
            Post.user: JOINED,
            Post.comments: (SUBQUERY, {Comment.user: SELECT_IN}),
        }
        eager_expr = SmartQueryMixin._eager_expr_from_schema(schema)
        post1 = await Post.options(*eager_expr).limit(1).unique_one()
        self.assertEqual('Bob Williams', post1.user.name)
        self.assertEqual('Bob Williams', post1.comments[0].user.name)

        schema = {Post.user: JOINED, Post.comments: {Comment.user: SELECT_IN}}
        eager_expr = SmartQueryMixin._eager_expr_from_schema(schema)
        post2 = await Post.options(*eager_expr).limit(1).unique_one()
        self.assertEqual('Bob Williams', post2.user.name)
        self.assertEqual('Bob Williams', post2.comments[0].user.name)

        with self.assertRaises(InvalidJoinMethodError):
            schema = {
                Post.user: JOINED,
                Post.comments: (SUBQUERY, {Comment.user: 'UNKNOWN'}),
            }
            SmartQueryMixin._eager_expr_from_schema(schema)

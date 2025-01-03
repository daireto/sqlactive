import asyncio
import unittest

from sqlalchemy.orm import joinedload
from sqlalchemy.exc import MultipleResultsFound

from sqlactive import JOINED, SUBQUERY, SELECT_IN
from sqlactive.async_query import AsyncQuery
from sqlactive.conn import DBConnection
from sqlactive.exceptions import NoSessionError

from ._logger import logger
from ._models import BaseModel, User, Post, Comment
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

    async def test_options(self):
        """Test for `options` function."""

        logger.info('Testing `options` function...')
        async_query = User._get_async_query()
        user = await async_query.options(joinedload(User.posts)).first()
        self.assertIsNotNone(user)
        if user:
            self.assertEqual('Lorem ipsum', user.posts[0].title)

    async def test_filter(self):
        """Test for `filter`, `where`, `find` functions."""

        logger.info('Testing `filter`, `where`, `find` functions...')
        async_query = User._get_async_query()
        user = await async_query.filter(username='Joe156').one()
        self.assertEqual('Joe Smith', user.name)

    async def test_order_by(self):
        """Test for `order_by`, `sort` functions."""

        logger.info('Testing `order_by`, `sort` functions...')
        async_query = User._get_async_query()
        users = await async_query.filter(username__like='Ji%').all()
        self.assertEqual('Jim32', users[0].username)
        users = await async_query.order_by(User.username).filter(username__like='Ji%').all()
        self.assertEqual('Jill874', users[0].username)
        async_query = Post._get_async_query()
        posts = await async_query.sort('-rating', 'user___name').all()
        self.assertEqual(24, len(posts))

    async def test_offset(self):
        """Test for `offset`, `skip` functions."""

        logger.info('Testing `offset`, `skip` functions...')
        async_query = User._get_async_query()
        users = await async_query.offset(1).filter(username__like='Ji%').all()
        self.assertEqual(2, len(users))
        users = await async_query.skip(2).filter(username__like='Ji%').all()
        self.assertEqual(1, len(users))

    async def test_limit(self):
        """Test for `limit`, `take` functions."""

        logger.info('Testing `limit`, `take` functions...')
        async_query = User._get_async_query()
        users = await async_query.limit(2).filter(username__like='Ji%').all()
        self.assertEqual(2, len(users))
        users = await async_query.take(1).filter(username__like='Ji%').all()
        self.assertEqual(1, len(users))

    async def test_join(self):
        """Test for `join` function."""

        logger.info('Testing `join` function...')
        async_query = User._get_async_query()
        users = await async_query.join(User.posts, (User.comments, True)).unique_all()
        USERS_THAT_HAVE_COMMENTS = [1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
        self.assertEqual(USERS_THAT_HAVE_COMMENTS, [user.id for user in users])
        self.assertEqual('Lorem ipsum dolor sit amet, consectetur adipiscing elit.', users[0].comments[0].body)

    async def test_with_subquery(self):
        """Test for `with_subquery` function."""

        logger.info('Testing `with_subquery` function...')
        async_query = User._get_async_query()
        users_count = len(await async_query.all())
        users = await async_query.with_subquery(User.posts, (User.comments, True)).all()
        self.assertEqual(users_count, len(users), 'message')
        self.assertEqual('Lorem ipsum dolor sit amet, consectetur adipiscing elit.', users[0].comments[0].body)

    async def test_with_schema(self):
        """Test for `with_schema` function."""

        logger.info('Testing `with_schema` function...')
        schema = {
            User.posts: JOINED,
            User.comments: (SUBQUERY, {Comment.post: SELECT_IN}),
        }
        async_query = User._get_async_query()
        user = await async_query.with_schema(schema).limit(1).unique_one()
        self.assertEqual('Lorem ipsum', user.comments[0].post.title)
        schema = {Post.user: JOINED, Post.comments: (SUBQUERY, {Comment.user: JOINED})}
        async_query = Post._get_async_query()
        post = await async_query.with_schema(schema).limit(1).unique_one()
        self.assertEqual('Bob Williams', post.user.name)
        self.assertEqual('Jill Peterson', post.comments[1].user.name)

    async def test_scalars(self):
        """Test for `scalars` function."""

        logger.info('Testing `scalars` function...')
        async_query = User._get_async_query()
        user_scalars = await async_query.scalars()
        users = user_scalars.all()
        self.assertEqual('Mike Turner', users[10].name)

    async def test_first(self):
        """Test for `first` function."""

        logger.info('Testing `first` function...')
        async_query = User._get_async_query()
        user = await async_query.first()
        self.assertIsNotNone(user)
        if user:
            self.assertEqual('Bob Williams', user.name)

    async def test_one(self):
        """Test for `one`, `fetch_one` functions."""

        logger.info('Testing `one`, `fetch_one` functions...')
        async_query = User._get_async_query()
        with self.assertRaises(MultipleResultsFound) as context:
            await async_query.one()
        with self.assertRaises(MultipleResultsFound) as context:
            await async_query.fetch_one()
        self.assertEqual('Multiple rows were found when exactly one was required', str(context.exception))
        user = await async_query.filter(username='Joe156').fetch_one()
        self.assertEqual('Joe Smith', user.name)

    async def test_one_or_none(self):
        """Test for `one_or_none`, `fetch_one_or_none` functions."""

        logger.info('Testing `one_or_none`, `fetch_one_or_none` functions...')
        async_query = User._get_async_query()
        with self.assertRaises(MultipleResultsFound) as context:
            await async_query.one_or_none()
        with self.assertRaises(MultipleResultsFound) as context:
            await async_query.fetch_one_or_none()
        self.assertEqual('Multiple rows were found when one or none was required', str(context.exception))
        user = await async_query.filter(username='Joe156').fetch_one_or_none()
        self.assertIsNotNone(user)
        if user:
            self.assertEqual('Joe Smith', user.name)
        user = await async_query.filter(username='Unknown').one_or_none()
        self.assertIsNone(user)

    async def test_all(self):
        """Test for `all`, `fetch_all`, `to_list` functions."""

        logger.info('Testing `all`, `fetch_all`, `to_list` functions...')
        async_query = User._get_async_query()
        users = await async_query.all()
        self.assertEqual(34, len(users))
        users = await async_query.fetch_all()
        self.assertEqual(34, len(users))
        users = await async_query.to_list()
        self.assertEqual(34, len(users))
        self.assertEqual('Mike Turner', users[10].name)

    async def test_unique(self):
        """Test for `unique` function."""

        logger.info('Testing `unique` function...')
        async_query = User._get_async_query()
        unique_user_scalars = await async_query.unique()
        users = unique_user_scalars.all()
        self.assertEqual('Mike Turner', users[10].name)

    async def test_unique_all(self):
        """Test for `unique_all` function."""

        logger.info('Testing `unique_all` function...')
        async_query = User._get_async_query()
        users = await async_query.unique_all()
        self.assertEqual('Mike Turner', users[10].name)

    async def test_unique_first(self):
        """Test for `unique_first` function."""

        logger.info('Testing `unique_first` function...')
        async_query = User._get_async_query()
        user = await async_query.unique_first()
        self.assertIsNotNone(user)
        if user:
            self.assertEqual('Bob Williams', user.name)

    async def test_unique_one(self):
        """Test for `unique_one` function."""

        logger.info('Testing `unique_one` function...')
        async_query = User._get_async_query()
        with self.assertRaises(MultipleResultsFound) as context:
            await async_query.unique_one()
        self.assertEqual('Multiple rows were found when exactly one was required', str(context.exception))
        user = await async_query.filter(username='Joe156').unique_one()
        self.assertEqual('Joe Smith', user.name)

    async def test_unique_one_or_none(self):
        """Test for `unique_one_or_none` function."""

        logger.info('Testing `unique_one_or_none` function...')
        async_query = User._get_async_query()
        with self.assertRaises(MultipleResultsFound) as context:
            await async_query.unique_one_or_none()
        self.assertEqual('Multiple rows were found when one or none was required', str(context.exception))
        user = await async_query.filter(username='Joe156').unique_one_or_none()
        self.assertIsNotNone(user)
        if user:
            self.assertEqual('Joe Smith', user.name)
        user = await async_query.filter(username='Unknown').unique_one_or_none()
        self.assertIsNone(user)

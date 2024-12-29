import asyncio
import unittest

from datetime import datetime, timezone
from sqlalchemy.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.operators import or_

from sqlactive import JOINED, SUBQUERY, SELECT_IN
from sqlactive.conn import DBConnection

from ._logger import logger
from ._models import User, Post, Comment
from ._seed import Seed


class TestActiveRecordMixin(unittest.IsolatedAsyncioTestCase):
    """Tests for `sqlactive.active_record.ActiveRecordMixin`."""

    DB_URL = 'sqlite+aiosqlite://'

    @classmethod
    def setUpClass(cls):
        logger.info('ActiveRecordMixin tests...')
        logger.info('Creating DB connection...')
        cls.conn = DBConnection(cls.DB_URL, echo=False)
        seed = Seed(cls.conn)
        asyncio.run(seed.run())

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'conn'):
            logger.info('Closing DB connection...')
            asyncio.run(cls.conn.close())

    def test_fill(self):
        """Test for `fill` function."""

        logger.info('Testing `fill` function...')
        user = User(username='Bob28', name='Bob', age=30)
        user.fill(**{'name': 'Bob Williams', 'age': 32})
        self.assertEqual('Bob28', user.username)
        self.assertEqual('Bob Williams', user.name)
        self.assertEqual(32, user.age)

    async def test_save(self):
        """Test for `save` function."""

        logger.info('Testing `save` function...')
        user = User(username='Test28', name='Test User', age=20)
        await user.save()
        now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')
        self.assertIsNotNone(user.id)
        self.assertEqual(now, user.created_at.strftime('%Y-%m-%d %H:%M'))
        self.assertEqual(now, user.updated_at.strftime('%Y-%m-%d %H:%M'))

    async def test_save_all(self):
        """Test for `save_all`function."""

        logger.info('Testing `save_all` function...')
        users = [
            User(username='Test100', name='Test User 1', age=20),
            User(username='Test200', name='Test User 2', age=30),
            User(username='Test300', name='Test User 3', age=40),
            User(username='Test400', name='Test User 4', age=20),
            User(username='Test500', name='Test User 5', age=30),
            User(username='Test600', name='Test User 6', age=40),
        ]
        user_ids = [user.id for user in users]
        for uid in user_ids:
            self.assertIsNone(uid)
        await User.save_all(users)
        now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')
        for user in users:
            self.assertIsNotNone(user.id)
            self.assertEqual(now, user.created_at.strftime('%Y-%m-%d %H:%M'))
            self.assertEqual(now, user.updated_at.strftime('%Y-%m-%d %H:%M'))

    async def test_create(self):
        """Test for `create`, `insert`, `add` functions."""

        logger.info('Testing `create`, `insert`, `add` functions...')
        user1 = await User.create(username='Test98', name='Test User 1', age=20)
        user2 = await User.insert(username='Test95', name='Test User 2', age=20)
        user3 = await User.add(username='Test92', name='Test User 3', age=20)
        now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')
        for user in [user1, user2, user3]:
            self.assertIsNotNone(user.id)
            self.assertEqual(now, user.created_at.strftime('%Y-%m-%d %H:%M'))
            self.assertEqual(now, user.updated_at.strftime('%Y-%m-%d %H:%M'))

    async def test_update(self):
        """Test for `update`, `edit` functions."""

        logger.info('Testing `update`, `edit` functions...')
        user = await User.get_or_fail(1)
        self.assertEqual('Bob Williams', user.name)
        await asyncio.sleep(1)
        await user.update(name='Bob Doe')
        self.assertGreater(user.updated_at, user.created_at)
        self.assertEqual('Bob Doe', user.name)
        await asyncio.sleep(1)
        await user.edit(age=32)
        self.assertEqual(32, user.age)

    async def test_create_all(self):
        """Test for `create_all`function."""

        logger.info(
            'Testing `create_all` function...'
        )
        users = [
            User(username='Test110', name='Test User 1', age=20),
            User(username='Test210', name='Test User 2', age=30),
            User(username='Test310', name='Test User 3', age=40),
            User(username='Test410', name='Test User 4', age=20),
            User(username='Test510', name='Test User 5', age=30),
            User(username='Test610', name='Test User 6', age=40),
            User(username='Test710', name='Test User 7', age=40),
            User(username='Test810', name='Test User 8', age=40),
            User(username='Test910', name='Test User 9', age=40),
            User(username='Test1010', name='Test User 10', age=40),
            User(username='Test1110', name='Test User 11', age=40),
            User(username='Test1210', name='Test User 12', age=40),
        ]
        user_ids = [user.id for user in users]
        for uid in user_ids:
            self.assertIsNone(uid)
        await User.create_all(users)
        now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')
        for user in users:
            self.assertIsNotNone(user.id)
            self.assertEqual(now, user.created_at.strftime('%Y-%m-%d %H:%M'))
            self.assertEqual(now, user.updated_at.strftime('%Y-%m-%d %H:%M'))

    async def test_update_all(self):
        """Test for `update_all` function."""

        logger.info('Testing `update_all` function...')
        users = [
            User(username='Test111', name='Test User 1', age=20),
            User(username='Test211', name='Test User 2', age=30),
            User(username='Test311', name='Test User 3', age=40),
            User(username='Test411', name='Test User 4', age=20),
            User(username='Test511', name='Test User 5', age=30),
            User(username='Test611', name='Test User 6', age=40),
            User(username='Test711', name='Test User 7', age=40),
            User(username='Test811', name='Test User 8', age=40),
        ]
        await User.create_all(users)
        for user in users:
            user.name = user.name.replace('Test User', 'Test User Updated')
        await asyncio.sleep(1)
        await User.update_all(users, refresh=True)
        for user in users:
            self.assertIn('Updated', user.name)
            self.assertGreater(user.updated_at, user.created_at)

    async def test_delete(self):
        """Test for `delete`, `remove` functions."""

        logger.info('Testing `delete`, `remove` functions...')
        user1 = await User.find(username='Lily9845').one()
        user2 = await User.find(username='Jessica3248').one()
        await user1.delete()
        await user2.remove()
        user1 = await User.find(username='Lily9845').one_or_none()
        user2 = await User.find(username='Jessica3248').one_or_none()
        self.assertIsNone(user1)
        self.assertIsNone(user2)

    async def test_delete_all(self):
        """Test for `delete_all` function."""

        logger.info('Testing `delete_all` function...')
        users = [
            User(username='DeleteTest121', name='Test User 1', age=20),
            User(username='DeleteTest221', name='Test User 2', age=30),
            User(username='DeleteTest321', name='Test User 3', age=40),
            User(username='DeleteTest421', name='Test User 4', age=20),
            User(username='DeleteTest521', name='Test User 5', age=30),
            User(username='DeleteTest621', name='Test User 6', age=40),
            User(username='DeleteTest721', name='Test User 7', age=40),
            User(username='DeleteTest821', name='Test User 8', age=40),
        ]
        await User.create_all(users)
        users = await User.find(username__startswith='DeleteTest').all()
        await User.delete_all(users)
        users = await User.find(username__startswith='DeleteTest').all()

    async def test_destroy(self):
        """Test for `destroy` function."""

        logger.info('Testing `destroy` function...')
        user1 = await User.get_or_fail(30)
        user2 = await User.get_or_fail(31)
        user3 = await User.get_or_fail(32)
        await User.destroy(user1.id, user2.id, user3.id)
        user1 = await User.get(30)
        user2 = await User.get(31)
        user3 = await User.get(32)
        self.assertIsNone(user1)
        self.assertIsNone(user2)
        self.assertIsNone(user3)

    async def test_get(self):
        """Test for `get` function."""

        logger.info('Testing `get` function...')
        user = await User.get(2)
        self.assertIsNotNone(user)
        if user:
            self.assertEqual('Bill65', user.username)

    async def test_get_or_fail(self):
        """Test for `get_or_fail` function."""

        logger.info('Testing `get_or_fail` function...')
        user = await User.get_or_fail(2)
        self.assertEqual('Bill65', user.username)
        with self.assertRaises(NoResultFound) as context:
            await User.get_or_fail(0)
        self.assertIn('User with id `0` was not found', str(context.exception))

    async def test_options(self):
        """Test for `options` function."""

        logger.info('Testing `options` function...')
        user = await User.options(joinedload(User.posts)).first()
        self.assertIsNotNone(user)
        if user:
            self.assertEqual('Lorem ipsum', user.posts[0].title)

    async def test_filter(self):
        """Test for `filter`, `where`, `find` functions."""

        logger.info('Testing `filter`, `where`, `find` functions...')
        user = await User.filter(username='Joe156').one()
        self.assertEqual('Joe Smith', user.name)
        user = await User.where(username='Jane54').one()
        self.assertEqual('Jane Doe', user.name)
        user = await User.find(username='John84').one()
        self.assertEqual('John Doe', user.name)

    async def test_find_one(self):
        """Test for `find_one` function."""

        logger.info('Testing `find_one` function...')
        user = await User.find_one(username='Joe156')
        self.assertEqual('Joe Smith', user.name)
        with self.assertRaises(NoResultFound) as context:
            await User.find_one(username='Unknown')
        self.assertEqual('No row was found when one was required', str(context.exception))

    async def test_find_one_or_none(self):
        """Test for `find_one_or_none` function."""

        logger.info('Testing `find_one_or_none` function...')
        user = await User.find_one_or_none(username='Joe156')
        self.assertIsNotNone(user)
        if user:
            self.assertEqual('Joe Smith', user.name)
        user = await User.find_one_or_none(username='Unknown')
        self.assertIsNone(user)

    async def test_find_all(self):
        """Test for `find_all` function."""

        logger.info('Testing `find_all` function...')
        users = await User.find_all(username__like='Ji%')
        self.assertEqual(3, len(users))

    async def test_order_by(self):
        """Test for `order_by`, `sort` functions."""

        logger.info('Testing `order_by`, `sort` functions...')
        users = await User.find(username__like='Ji%').all()
        self.assertEqual('Jim32', users[0].username)
        users = await User.find(username__like='Ji%').order_by(User.username).all()
        self.assertEqual('Jill874', users[0].username)
        users = await User.find(username__like='Ji%').sort(User.age).all()
        self.assertEqual('Jimmy156', users[0].username)

    async def test_offset(self):
        """Test for `offset`, `skip` functions."""

        logger.info('Testing `offset`, `skip` functions...')
        users = await User.find(username__like='Ji%').offset(1).all()
        self.assertEqual(2, len(users))
        users = await User.find(username__like='Ji%').skip(2).all()
        self.assertEqual(1, len(users))

    async def test_limit(self):
        """Test for `limit`, `take` functions."""

        logger.info('Testing `limit`, `take` functions...')
        users = await User.find(username__like='Ji%').limit(2).all()
        self.assertEqual(2, len(users))
        users = await User.find(username__like='Ji%').take(1).all()
        self.assertEqual(1, len(users))

    async def test_join(self):
        """Test for `join` function."""

        logger.info('Testing `join` function...')
        users = await User.join(User.posts, (User.comments, True)).unique_all()
        USERS_THAT_HAVE_COMMENTS = [1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
        self.assertEqual(USERS_THAT_HAVE_COMMENTS, [user.id for user in users])
        self.assertEqual('Lorem ipsum dolor sit amet, consectetur adipiscing elit.', users[0].comments[0].body)

    async def test_with_subquery(self):
        """Test for `with_subquery` function."""

        logger.info('Testing `with_subquery` function...')
        users_count = len(await User.all())
        users = await User.with_subquery(User.posts, (User.comments, True)).all()
        self.assertEqual(users_count, len(users), 'message')
        self.assertEqual('Lorem ipsum dolor sit amet, consectetur adipiscing elit.', users[0].comments[0].body)

    async def test_with_schema(self):
        """Test for `with_schema` function."""

        logger.info('Testing `with_schema` function...')
        schema = {
            User.posts: JOINED,
            User.comments: (SUBQUERY, {Comment.post: SELECT_IN}),
        }
        user = await User.with_schema(schema).limit(1).unique_one()
        self.assertEqual('Lorem ipsum', user.comments[0].post.title)
        schema = {Post.user: JOINED, Post.comments: (SUBQUERY, {Comment.user: JOINED})}
        post = await Post.with_schema(schema).limit(1).unique_one()
        self.assertEqual('Bob Doe', post.user.name)
        self.assertEqual('Jill Peterson', post.comments[1].user.name)

    async def test_scalars(self):
        """Test for `scalars` function."""

        logger.info('Testing `scalars` function...')
        user_scalars = await User.scalars()
        users = user_scalars.all()
        self.assertEqual('Mike Turner', users[10].name)

    async def test_first(self):
        """Test for `first` function."""

        logger.info('Testing `first` function...')
        user = await User.first()
        self.assertIsNotNone(user)
        if user:
            self.assertEqual('Bob Williams', user.name)

    async def test_one(self):
        """Test for `one`, `fetch_one` functions."""

        logger.info('Testing `one`, `fetch_one` functions...')
        with self.assertRaises(MultipleResultsFound) as context:
            await User.one()
        self.assertEqual('Multiple rows were found when exactly one was required', str(context.exception))
        user = await User.find(username='Joe156').fetch_one()
        self.assertEqual('Joe Smith', user.name)

    async def test_one_or_none(self):
        """Test for `one_or_none`, `fetch_one_or_none` functions."""

        logger.info('Testing `one_or_none`, `fetch_one_or_none` functions...')
        with self.assertRaises(MultipleResultsFound) as context:
            await User.one_or_none()
        self.assertEqual('Multiple rows were found when one or none was required', str(context.exception))
        user = await User.find(username='Joe156').fetch_one_or_none()
        self.assertIsNotNone(user)
        if user:
            self.assertEqual('Joe Smith', user.name)
        user = await User.find(username='Unknown').one_or_none()
        self.assertIsNone(user)

    async def test_all(self):
        """Test for `all`, `fetch_all`, `to_list` functions."""

        logger.info('Testing `all`, `fetch_all`, `to_list` functions...')
        users = await User.all()
        self.assertEqual(34, len(users))
        self.assertEqual('Mike Turner', users[10].name)
        users = await User.where(username__like='Ji%').fetch_all()
        self.assertEqual(3, len(users))
        posts = await Post.where(rating=3).to_list()
        self.assertEqual(5, len(posts))

    async def test_unique(self):
        """Test for `unique` function."""

        logger.info('Testing `unique` function...')
        unique_user_scalars = await User.unique()
        users = unique_user_scalars.all()
        self.assertEqual('Mike Turner', users[10].name)

    async def test_unique_all(self):
        """Test for `unique_all` function."""

        logger.info('Testing `unique_all` function...')
        users = await User.unique_all()
        self.assertEqual('Mike Turner', users[10].name)

    async def test_unique_first(self):
        """Test for `unique_first` function."""

        logger.info('Testing `unique_first` function...')
        user = await User.unique_first()
        self.assertIsNotNone(user)
        if user:
            self.assertEqual('Bob Williams', user.name)

    async def test_unique_one(self):
        """Test for `unique_one` function."""

        logger.info('Testing `unique_one` function...')
        with self.assertRaises(MultipleResultsFound) as context:
            await User.unique_one()
        self.assertEqual('Multiple rows were found when exactly one was required', str(context.exception))
        user = await User.find(username='Joe156').unique_one()
        self.assertEqual('Joe Smith', user.name)

    async def test_unique_one_or_none(self):
        """Test for `unique_one_or_none` function."""

        logger.info('Testing `unique_one_or_none` function...')
        with self.assertRaises(MultipleResultsFound) as context:
            await User.unique_one_or_none()
        self.assertEqual('Multiple rows were found when one or none was required', str(context.exception))
        user = await User.find(username='Joe156').unique_one_or_none()
        self.assertIsNotNone(user)
        if user:
            self.assertEqual('Joe Smith', user.name)
        user = await User.find(username='Unknown').unique_one_or_none()
        self.assertIsNone(user)

    async def test_smart_query(self):
        """Test for `smart_query` function."""

        logger.info('Testing `smart_query` function...')
        query = User.smart_query(
            criterion=(or_(User.age == 30, User.age == 32),),
            filters={'username__like': '%8'},
            sort_columns=(User.username,),
            sort_attrs=('age',),
            schema={User.posts: JOINED, User.comments: (SUBQUERY, {Comment.post: SELECT_IN})},
        )
        users = await query.unique_all()
        self.assertEqual(['Bob28', 'Ian48'], [user.username for user in users])

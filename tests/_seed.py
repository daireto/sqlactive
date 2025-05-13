"""``Seed`` class to seed database with test data."""

from sqlactive.base_model import ActiveRecordBaseModel
from sqlactive.conn import DBConnection

from ._logger import logger
from ._models import Comment, Post, Product, Sell, User


class Seed:
    def __init__(
        self,
        conn: DBConnection,
        base_model: type[ActiveRecordBaseModel] | None = None,
    ):
        """Creates a new seeder.

        Parameters
        ----------
        conn : DBConnection
            Database connection.
        base_model : type[ActiveRecordBaseModel], optional
            Base model class, by default ActiveRecordBaseModel.
        """
        self.conn = conn
        self.base_model = base_model

    async def run(self):
        """Seeds the database with test data."""
        logger.info('Initializing database...')
        await self.conn.init_db(self.base_model)
        logger.info('Seeding users...')
        await self.seed_users()
        logger.info('Seeding posts...')
        await self.seed_posts()
        logger.info('Seeding comments...')
        await self.seed_comments()
        logger.info('Seeding products...')
        await self.seed_products()
        logger.info('Seeding sells...')
        await self.seed_sells()
        logger.info('Database seeded.')

    async def seed_users(self):
        """Seeds the database with test users."""
        await User.insert_all(
            [
                User(username='Bob28', name='Bob Williams', age=30),
                User(username='Bill65', name='Bill Smith', age=40),
                User(username='Joe156', name='Joe Smith', age=26),
                User(username='Jane54', name='Jane Doe', age=25),
                User(username='John84', name='John Doe', age=19),
                User(username='Jenny654', name='Jenny Wayne', age=35),
                User(username='Jim32', name='Jim Collins', age=36),
                User(username='Jimmy156', name='Jimmy Henderson', age=27),
                User(username='Maria564', name='Maria Tillman', age=28),
                User(username='Jill874', name='Jill Peterson', age=34),
                User(username='Mike54', name='Mike Turner', age=29),
                User(username='Molly565', name='Molly Anderson', age=30),
                User(username='Alice5262', name='Alice Anderson', age=24),
                User(username='David32', name='David Washington', age=25),
                User(username='Helen12', name='Helen Walker', age=31),
                User(username='Diana84', name='Diana Johnson', age=26),
                User(username='Frank564', name='Frank Gardner', age=28),
                User(username='Jack321', name='Jack Sparrow', age=33),
                User(username='George3241', name='George Washington', age=29),
                User(username='Harry847', name='Harry Potter', age=30),
                User(username='Ian48', name='Ian Levitt', age=32),
                User(username='Edward7656', name='Edward Norton', age=27),
                User(username='Johnny665', name='Johnny Depp', age=28),
                User(username='Tom897', name='Tom Cruise', age=35),
                User(username='Brad654', name='Brad Pitt', age=36),
                User(username='Angel8499', name='Angel Eyes', age=31),
                User(username='Bruce984', name='Bruce Willis', age=33),
                User(username='Matt954', name='Matt Damon', age=30),
                User(username='George341854', name='George Mason', age=29),
                User(username='Emily894', name='Emily Watson', age=27),
                User(username='Kate6485', name='Kate Middleton', age=28),
                User(username='Jennifer5215', name='Jennifer Lawrence', age=31),
                User(username='Jessica3248', name='Jessica Alba', age=30),
                User(username='Lily9845', name='Lily Collins', age=29),
            ]
        )

    async def seed_posts(self):
        """Seeds the database with test posts."""
        await Post.insert_all(
            [
                Post(
                    title='Lorem ipsum',
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    rating=4,
                    user_id=1,
                ),
                Post(
                    title='Lorem ipsum',
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    rating=3,
                    user_id=2,
                ),
                Post(
                    title='Lorem ipsum',
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    rating=2,
                    user_id=3,
                ),
                Post(
                    title='Lorem ipsum',
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    rating=1,
                    user_id=4,
                ),
                Post(
                    title='Lorem ipsum',
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    rating=5,
                    user_id=5,
                ),
                Post(
                    title='Lorem ipsum',
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    rating=4,
                    user_id=6,
                ),
                Post(
                    title='Lorem ipsum',
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    rating=3,
                    user_id=7,
                ),
                Post(
                    title='Lorem ipsum',
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    rating=2,
                    user_id=8,
                ),
                Post(
                    title='Lorem ipsum',
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    rating=1,
                    user_id=9,
                ),
                Post(
                    title='Lorem ipsum',
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    rating=5,
                    user_id=10,
                ),
                Post(
                    title='Lorem ipsum',
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    rating=4,
                    user_id=11,
                ),
                Post(
                    title='Lorem ipsum',
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    rating=3,
                    user_id=12,
                ),
                Post(
                    title='Lorem ipsum',
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    rating=2,
                    user_id=13,
                ),
                Post(
                    title='Lorem ipsum',
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    rating=1,
                    user_id=14,
                ),
                Post(
                    title='Lorem ipsum',
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    rating=5,
                    user_id=15,
                ),
                Post(
                    title='Lorem ipsum',
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    rating=4,
                    user_id=16,
                ),
                Post(
                    title='Lorem ipsum',
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    rating=3,
                    user_id=17,
                ),
                Post(
                    title='Lorem ipsum',
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    rating=2,
                    user_id=18,
                ),
                Post(
                    title='Lorem ipsum',
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    rating=1,
                    user_id=19,
                ),
                Post(
                    title='Lorem ipsum',
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    rating=5,
                    user_id=20,
                ),
                Post(
                    title='Lorem ipsum',
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    rating=4,
                    user_id=21,
                ),
                Post(
                    title='Lorem ipsum',
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    rating=3,
                    user_id=22,
                ),
                Post(
                    title='Lorem ipsum',
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    rating=2,
                    user_id=23,
                ),
                Post(
                    title='Lorem ipsum',
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    rating=1,
                    user_id=24,
                ),
            ]
        )

    async def seed_comments(self):
        """Seeds the database with test comments."""
        await Comment.insert_all(
            [
                Comment(
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    post_id=1,
                    user_id=1,
                ),
                Comment(
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    post_id=2,
                    user_id=1,
                ),
                Comment(
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    post_id=2,
                    user_id=2,
                ),
                Comment(
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    post_id=3,
                    user_id=2,
                ),
                Comment(
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    post_id=4,
                    user_id=4,
                ),
                Comment(
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    post_id=4,
                    user_id=5,
                ),
                Comment(
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    post_id=4,
                    user_id=6,
                ),
                Comment(
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    post_id=4,
                    user_id=7,
                ),
                Comment(
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    post_id=7,
                    user_id=7,
                ),
                Comment(
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    post_id=7,
                    user_id=8,
                ),
                Comment(
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    post_id=7,
                    user_id=9,
                ),
                Comment(
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    post_id=1,
                    user_id=10,
                ),
                Comment(
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    post_id=2,
                    user_id=11,
                ),
                Comment(
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    post_id=9,
                    user_id=11,
                ),
                Comment(
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    post_id=9,
                    user_id=12,
                ),
                Comment(
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    post_id=9,
                    user_id=13,
                ),
                Comment(
                    body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                    post_id=9,
                    user_id=14,
                ),
            ]
        )

    async def seed_products(self):
        """Seeds the database with test products."""
        await Product.insert_all(
            [
                Product(name='Product 1', description='Description 1', price=10.0),
                Product(name='Product 2', description='Description 2', price=20.0),
                Product(name='Product 3', description='Description 3', price=30.0),
                Product(name='Product 4', description='Description 4', price=40.0),
                Product(name='Product 5', description='Description 5', price=50.0),
                Product(name='Product 6', description='Description 6', price=60.0),
                Product(name='Product 7', description='Description 7', price=70.0),
                Product(name='Product 8', description='Description 8', price=80.0),
            ]
        )

    async def seed_sells(self):
        """Seeds the database with test sells."""
        await Sell.insert_all(
            [
                Sell(id=1, product_id=1, quantity=2),
                Sell(id=2, product_id=2, quantity=2),
                Sell(id=3, product_id=3, quantity=5),
                Sell(id=4, product_id=4, quantity=4),
                Sell(id=5, product_id=5, quantity=3),
                Sell(id=6, product_id=6, quantity=4),
                Sell(id=7, product_id=7, quantity=1),
                Sell(id=8, product_id=8, quantity=4),
            ]
        )

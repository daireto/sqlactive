import asyncio
import unittest

from sqlactive.conn import DBConnection
from sqlactive.exceptions import CompositePrimaryKeyError, RelationError

from ._logger import logger
from ._models import BaseModel, Comment, Post, Product, Sell, User
from ._seed import Seed


class TestInspectionMixin(unittest.IsolatedAsyncioTestCase):
    """Tests for ``sqlactive.inspection.InspectionMixin``."""

    DB_URL = 'sqlite+aiosqlite://'

    @classmethod
    def setUpClass(cls):
        logger.info('***** InspectionMixin tests *****')
        logger.info('Creating DB connection...')
        cls.conn = DBConnection(cls.DB_URL, echo=False)
        seed = Seed(cls.conn, BaseModel)
        asyncio.run(seed.run())

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'conn'):
            logger.info('Closing DB connection...')
            asyncio.run(cls.conn.close(BaseModel))

    async def test_repr(self):
        """Test for ``__repr__`` function."""
        logger.info('Testing "__repr__" function...')
        user = await User.get_or_fail(1)
        self.assertEqual('User(id=1)', repr(user))
        users = await User.find(name__endswith='Doe').all()
        self.assertEqual('[User(id=4), User(id=5)]', repr(users))

    async def test_id_str(self):
        """Test for ``id_str`` property."""
        logger.info('Testing "id_str" property...')
        user = await User.get_or_fail(1)
        self.assertEqual('id=1', user.id_str)
        sell = await Sell.limit(1).one()
        self.assertEqual('id=1, product_id=1', sell.id_str)
        unknown_sell = Sell(id=1, product_id=1)
        self.assertEqual('id=1, product_id=1', unknown_sell.id_str)

    def test_columns(self):
        """Test for ``columns`` classproperty."""
        logger.info('Testing "columns" classproperty...')
        self.assertCountEqual(
            ['id', 'username', 'name', 'age', 'created_at', 'updated_at'],
            User.columns,
        )

    def test_primary_keys(self):
        """Test for ``primary_keys`` classproperty."""
        logger.info('Testing "primary_keys" classproperty...')
        self.assertCountEqual(['id'], User.primary_keys)

    def test_primary_key_name(self):
        """Test for ``primary_key_name`` classproperty."""
        logger.info('Testing "primary_key_name" classproperty...')
        with self.assertRaises(CompositePrimaryKeyError):
            _ = Sell.primary_key_name

    def test_relations(self):
        """Test for ``relations`` classproperty."""
        logger.info('Testing "relations" classproperty...')
        self.assertCountEqual(['posts', 'comments'], User.relations)

    def test_settable_relations(self):
        """Test for ``settable_relations`` classproperty."""
        logger.info('Testing "settable_relations" classproperty...')
        self.assertCountEqual(['posts', 'comments'], User.settable_relations)
        self.assertEqual(0, len(Product.settable_relations))

    def test_hybrid_properties(self):
        """Test for ``hybrid_properties`` classproperty."""
        logger.info('Testing "hybrid_properties" classproperty...')
        self.assertCountEqual(['is_adult'], User.hybrid_properties)

    def test_hybrid_methods(self):
        """Test for ``hybrid_methods`` classproperty."""
        logger.info('Testing "hybrid_methods" classproperty...')
        self.assertCountEqual(['older_than'], User.hybrid_methods)
        self.assertTrue(User(age=35).older_than(User(age=30)))
        self.assertFalse(User(age=20).older_than(User(age=30)))

    def test_filterable_attributes(self):
        """Test for ``filterable_attributes`` classproperty."""
        logger.info('Testing "filterable_attributes" classproperty...')
        self.assertCountEqual(
            [
                'posts',
                'comments',
                'id',
                'username',
                'name',
                'age',
                'created_at',
                'updated_at',
                'is_adult',
                'older_than',
            ],
            User.filterable_attributes,
        )

    def test_sortable_attributes(self):
        """Test for ``sortable_attributes`` classproperty."""
        logger.info('Testing "sortable_attributes" classproperty...')
        self.assertCountEqual(
            [
                'id',
                'username',
                'name',
                'age',
                'created_at',
                'updated_at',
                'is_adult',
            ],
            User.sortable_attributes,
        )

    def test_settable_attributes(self):
        """Test for ``settable_attributes`` classproperty."""
        logger.info('Testing "settable_attributes" classproperty...')
        self.assertCountEqual(
            [
                'id',
                'username',
                'name',
                'age',
                'created_at',
                'updated_at',
                'is_adult',
                'posts',
                'comments',
            ],
            User.settable_attributes,
        )

    def test_searchable_attributes(self):
        """Test for ``searchable_attributes`` classproperty."""
        logger.info('Testing "searchable_attributes" classproperty...')
        self.assertCountEqual(['username', 'name'], User.searchable_attributes)

    def test_get_class_of_relation(self):
        """Test for ``get_class_of_relation`` function."""
        logger.info('Testing "get_class_of_relation" function...')
        self.assertEqual(Post, User.get_class_of_relation('posts'))
        self.assertEqual(Comment, User.get_class_of_relation('comments'))
        self.assertEqual(Product, Sell.get_class_of_relation('product'))
        with self.assertRaises(RelationError):
            User.get_class_of_relation('sells')

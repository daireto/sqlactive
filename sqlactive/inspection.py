"""This module defines ``InspectionMixin`` class."""

from numbers import Number
from typing import Any

from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.orm import DeclarativeBase, RelationshipProperty
from sqlalchemy.sql.schema import Column
from typing_extensions import Self

from .exceptions import CompositePrimaryKeyError, RelationError
from .utils import classproperty


class InspectionMixin(DeclarativeBase):
    """Mixin for SQLAlchemy models to provide inspection methods
    for attributes and properties.
    """

    __abstract__ = True

    @property
    def id_str(self) -> str:
        """Returns a string representation of the primary key.

        If the primary key is composite, returns a comma-separated
        list of key-value pairs.

        Examples
        --------
        Assume two models ``User`` and ``Sell``:
        >>> from sqlactive import ActiveRecordBaseModel
        >>> class User(ActiveRecordBaseModel):
        ...     __tablename__ = 'users'
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     username: Mapped[str] = mapped_column()
        >>> class Sell(ActiveRecordBaseModel):
        ...     __tablename__ = 'sells'
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     product_id: Mapped[int] = mapped_column(
        ...         ForeignKey('products.id'), primary_key=True
        ...     )

        Usage:
        >>> user = User.insert(name='Bob')
        >>> user.id_str
        'id=1'
        >>> sell = Sell(id=1, product_id=1)
        >>> sell.id_str
        'id=1, product_id=1'
        """
        mapped = []
        for pk in self.primary_keys_full:
            value = getattr(self, pk.key)
            mapped.append(
                f'{pk.key}={value}'
                if isinstance(value, Number) or value is None
                else f'{pk.key}="{value}"'
            )
        return ', '.join(mapped)

    @classproperty
    def columns(cls) -> list[str]:
        """Returns a list of column names.

        Examples
        --------
        Assume a model ``User``:
        >>> from sqlactive import ActiveRecordBaseModel
        >>> class User(ActiveRecordBaseModel):
        ...     __tablename__ = 'users'
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     username: Mapped[str] = mapped_column()
        ...     name: Mapped[str] = mapped_column()
        ...     age: Mapped[int] = mapped_column()

        Usage:
        >>> User.columns
        ['id', 'username', 'name', 'age', 'created_at', 'updated_at']
        """
        return cls.__table__.columns.keys()

    @classproperty
    def string_columns(cls) -> list[str]:
        """Returns a list of string column names.

        Examples
        --------
        Assume a model ``User``:
        >>> from sqlactive import ActiveRecordBaseModel
        >>> class User(ActiveRecordBaseModel):
        ...     __tablename__ = 'users'
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     username: Mapped[str] = mapped_column()
        ...     name: Mapped[str] = mapped_column()
        ...     age: Mapped[int] = mapped_column()

        Usage:
        >>> User.string_columns
        ['username', 'name']
        """
        return [
            c.key for c in cls.__table__.columns if c.type.python_type is str
        ]

    @classproperty
    def primary_keys_full(cls) -> tuple[Column[Any], ...]:
        """Returns the columns that form the primary key.

        Examples
        --------
        Assume a model ``User``:
        >>> from sqlactive import ActiveRecordBaseModel
        >>> class User(ActiveRecordBaseModel):
        ...     __tablename__ = 'users'
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     username: Mapped[str] = mapped_column()

        Usage:
        >>> User.primary_keys_full
        (Column('id', Integer(), table=<users>, primary_key=True, nullable=False),)
        """
        return cls.__mapper__.primary_key

    @classproperty
    def primary_keys(cls) -> list[str]:
        """Returns the names of the primary key columns.

        Examples
        --------
        Assume a model ``User``:
        >>> from sqlactive import ActiveRecordBaseModel
        >>> class User(ActiveRecordBaseModel):
        ...     __tablename__ = 'users'
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     username: Mapped[str] = mapped_column()

        Usage:
        >>> User.primary_keys
        ['id']
        """
        return [pk.key for pk in cls.primary_keys_full]

    @classproperty
    def primary_key_name(cls) -> str:
        """Returns the primary key name of the model.

        .. warning::
            This property can only be used if the model has a single
            primary key. If the model has a composite primary key,
            an ``CompositePrimaryKeyError`` is raised.

        Raises
        ------
        CompositePrimaryKeyError
            If the model has a composite primary key.

        Examples
        --------
        Assume a model ``User``:
        >>> from sqlactive import ActiveRecordBaseModel
        >>> class User(ActiveRecordBaseModel):
        ...     __tablename__ = 'users'
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     username: Mapped[str] = mapped_column()

        Usage:
        >>> User.primary_key_name
        'id'

        Assume a model ``Sell``:
        >>> from sqlactive import ActiveRecordBaseModel
        >>> class Sell(ActiveRecordBaseModel):
        ...     __tablename__ = 'sells'
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     product_id: Mapped[int] = mapped_column(primary_key=True)
        ...     quantity: Mapped[int] = mapped_column()

        An error is raised:
        >>> Sell.primary_key_name
        Traceback (most recent call last):
        ...
        CompositePrimaryKeyError: model 'Sell' has a composite primary key
        """
        if len(cls.primary_keys) > 1:
            raise CompositePrimaryKeyError(cls.__name__)

        return cls.primary_keys[0]

    @classproperty
    def relations(cls) -> list[str]:
        """Returns a list of relationship names.

        Examples
        --------
        Assume a model ``User``:
        >>> from sqlactive import ActiveRecordBaseModel
        >>> class User(ActiveRecordBaseModel):
        ...     __tablename__ = 'users'
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     # other columns
        ...     posts: Mapped[list['Post']] = relationship(
        ...         back_populates='user'
        ...     )
        ...     comments: Mapped[list['Comment']] = relationship(
        ...         back_populates='user'
        ...     )

        Usage:
        >>> User.relations
        ['posts', 'comments']
        """
        return [
            c.key
            for c in cls.__mapper__.attrs
            if isinstance(c, RelationshipProperty)
        ]

    @classproperty
    def settable_relations(cls) -> list[str]:
        """Returns a list of settable (not viewonly) relationship names.

        Examples
        --------
        Assume a model ``User``:
        >>> from sqlactive import ActiveRecordBaseModel
        >>> class User(ActiveRecordBaseModel):
        ...     __tablename__ = 'users'
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     # other columns
        ...     posts: Mapped[list['Post']] = relationship(
        ...         back_populates='user'
        ...     )
        ...     comments: Mapped[list['Comment']] = relationship(
        ...         back_populates='user'
        ...     )

        Usage:
        >>> User.settable_relations
        ['posts', 'comments']

        Assume a model ``Product``:
        >>> from sqlactive import ActiveRecordBaseModel
        >>> class Product(BaseModel):
        ...     __tablename__ = 'products'
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     # other columns
        ...     sells: Mapped[list['Sell']] = relationship(
        ...         back_populates='product',
        ...         viewonly=True  # Not settable
        ...     )

        Usage:
        >>> Product.settable_relations
        []
        """
        return [
            r for r in cls.relations if not getattr(cls, r).property.viewonly
        ]

    @classproperty
    def hybrid_properties(cls) -> list[str]:
        """Returns a list of hybrid property names.

        Examples
        --------
        Assume a model ``User``:
        >>> from sqlactive import ActiveRecordBaseModel
        >>> class User(ActiveRecordBaseModel):
        ...     __tablename__ = 'users'
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     # other columns
        ...     posts: Mapped[list['Post']] = relationship(
        ...         back_populates='user'
        ...     )
        ...     comments: Mapped[list['Comment']] = relationship(
        ...         back_populates='user'
        ...     )
        ...     @hybrid_property
        ...     def is_adult(self):
        ...         return self.age > 18

        Usage:
        >>> User.hybrid_properties
        ['is_adult']
        """
        items = cls.__mapper__.all_orm_descriptors
        return [
            item.__name__
            for item in items
            if isinstance(item, hybrid_property)
        ]

    @classproperty
    def hybrid_methods_full(cls) -> dict[str, hybrid_method[..., Any]]:
        """Returns a dict of hybrid methods.

        Examples
        --------
        Assume a model ``User``:
        >>> from sqlactive import ActiveRecordBaseModel
        >>> class User(ActiveRecordBaseModel):
        ...     __tablename__ = 'users'
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     # other columns
        ...     posts: Mapped[list['Post']] = relationship(
        ...         back_populates='user'
        ...     )
        ...     comments: Mapped[list['Comment']] = relationship(
        ...         back_populates='user'
        ...     )
        ...     @hybrid_method
        ...     def older_than(self, other: 'User'):
        ...         return self.age > other.age

        Usage:
        >>> User.hybrid_methods_full
        {'older_than': hybrid_method(...)}
        """
        items = cls.__mapper__.all_orm_descriptors
        return {
            item.func.__name__: item
            for item in items
            if type(item) is hybrid_method
        }

    @classproperty
    def hybrid_methods(cls) -> list[str]:
        """Returns a list of hybrid method names.

        Examples
        --------
        Assume a model ``User``:
        >>> from sqlactive import ActiveRecordBaseModel
        >>> class User(ActiveRecordBaseModel):
        ...     __tablename__ = 'users'
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     # other columns
        ...     posts: Mapped[list['Post']] = relationship(
        ...         back_populates='user'
        ...     )
        ...     comments: Mapped[list['Comment']] = relationship(
        ...         back_populates='user'
        ...     )
        ...     @hybrid_method
        ...     def older_than(self, other: 'User'):
        ...         return self.age > other.age

        Usage:
        >>> User.hybrid_methods
        ['older_than']
        """
        return list(cls.hybrid_methods_full.keys())

    @classproperty
    def filterable_attributes(cls) -> list[str]:
        """Returns a list of filterable attributes.

        These are all columns, relations, hybrid properties
        and hybrid methods.

        Examples
        --------
        Assume a model ``User``:
        >>> from sqlactive import ActiveRecordBaseModel
        >>> class User(ActiveRecordBaseModel):
        ...     __tablename__ = 'users'
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     username: Mapped[str] = mapped_column()
        ...     name: Mapped[str] = mapped_column()
        ...     age: Mapped[int] = mapped_column()
        ...     posts: Mapped[list['Post']] = relationship(
        ...         back_populates='user'
        ...     )
        ...     comments: Mapped[list['Comment']] = relationship(
        ...         back_populates='user'
        ...     )
        ...     @hybrid_property
        ...     def is_adult(self):
        ...         return self.age > 18
        ...     @hybrid_method
        ...     def older_than(self, other: 'User'):
        ...         return self.age > other.age

        Usage:
        >>> User.filterable_attributes
        ['id', 'username', 'name', 'age', 'created_at', 'updated_at', 'posts', 'comments', 'is_adult', 'older_than']
        """
        return (
            cls.columns
            + cls.relations
            + cls.hybrid_properties
            + cls.hybrid_methods
        )

    @classproperty
    def sortable_attributes(cls) -> list[str]:
        """Returns a list of sortable attributes.

        These are all columns and hybrid properties.

        Examples
        --------
        Assume a model ``User``:
        >>> from sqlactive import ActiveRecordBaseModel
        >>> class User(ActiveRecordBaseModel):
        ...     __tablename__ = 'users'
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     username: Mapped[str] = mapped_column()
        ...     name: Mapped[str] = mapped_column()
        ...     age: Mapped[int] = mapped_column()
        ...     posts: Mapped[list['Post']] = relationship(
        ...         back_populates='user'
        ...     )
        ...     comments: Mapped[list['Comment']] = relationship(
        ...         back_populates='user'
        ...     )
        ...     @hybrid_property
        ...     def is_adult(self):
        ...         return self.age > 18

        Usage:
        >>> User.sortable_attributes
        ['id', 'username', 'name', 'age', 'created_at', 'updated_at', 'is_adult']
        """
        return cls.columns + cls.hybrid_properties

    @classproperty
    def settable_attributes(cls) -> list[str]:
        """Returns a list of settable attributes.

        These are all columns, settable relations and hybrid properties.

        Examples
        --------
        Assume a model ``User``:
        >>> from sqlactive import ActiveRecordBaseModel
        >>> class User(ActiveRecordBaseModel):
        ...     __tablename__ = 'users'
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     username: Mapped[str] = mapped_column()
        ...     name: Mapped[str] = mapped_column()
        ...     age: Mapped[int] = mapped_column()
        ...     posts: Mapped[list['Post']] = relationship(
        ...         back_populates='user'
        ...     )
        ...     comments: Mapped[list['Comment']] = relationship(
        ...         back_populates='user'
        ...     )
        ...     @hybrid_property
        ...     def is_adult(self):
        ...         return self.age > 18

        Usage:
        >>> User.settable_attributes
        ['username', 'name', 'age', 'created_at', 'updated_at', 'posts', 'comments', 'is_adult']
        """
        return cls.columns + cls.settable_relations + cls.hybrid_properties

    @classproperty
    def searchable_attributes(cls) -> list[str]:
        """Returns a list of searchable attributes.

        These are all string columns.

        Examples
        --------
        Assume a model ``User``:
        >>> from sqlactive import ActiveRecordBaseModel
        >>> class User(ActiveRecordBaseModel):
        ...     __tablename__ = 'users'
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     username: Mapped[str] = mapped_column()
        ...     name: Mapped[str] = mapped_column()
        ...     age: Mapped[int] = mapped_column()

        Usage:
        >>> User.searchable_attributes
        ['username', 'name']
        """
        return cls.string_columns

    @classmethod
    def get_class_of_relation(cls, relation_name: str) -> type[Self]:
        """Gets the class of a relationship by its name.

        Parameters
        ----------
        relation_name : str
            The name of the relationship.

        Raises
        ------
        RelationError
            If the relation is not found.

        Examples
        --------
        Assume a model ``User``:
        >>> from sqlactive import ActiveRecordBaseModel
        >>> class User(ActiveRecordBaseModel):
        ...     __tablename__ = 'users'
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     # other columns
        ...     posts: Mapped[list['Post']] = relationship(
        ...         back_populates='user'
        ...     )
        ...     comments: Mapped[list['Comment']] = relationship(
        ...         back_populates='user'
        ...     )

        Usage:
        >>> User.get_class_of_relation('posts')
        <class 'Post'>
        >>> User.get_class_of_relation('comments')
        <class 'Comment'>
        >>> User.get_class_of_relation('sells')
        Traceback (most recent call last):
            ...
        RelationError: no such relation: 'sells' in model 'User'
        """
        try:
            return cls.__mapper__.relationships[relation_name].mapper.class_
        except KeyError:
            raise RelationError(relation_name, cls.__name__)

    def __repr__(self) -> str:
        """Returns a string representation of the model.

        Representation format is
        ``ClassName(pk1=value1, pk2=value2, ...)``

        Examples
        --------
        Assume a model ``User`` with a primary key ``id``:
        >>> user = User.insert(name='Bob')
        >>> user
        User(id=1)
        >>> users = await User.find(name__endswith='Doe').all()
        >>> users
        [User(id=4), User(id=5)]
        """
        return f'{self.__class__.__name__}({self.id_str})'

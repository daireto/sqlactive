"""This module defines ``InspectionMixin`` class."""

from numbers import Number
from typing import Any

from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.orm import DeclarativeBase, RelationshipProperty
from sqlalchemy.sql.schema import Column
from typing_extensions import Self

from .utils import classproperty


class InspectionMixin(DeclarativeBase):
    """Mixin for SQLAlchemy models to provide inspection methods
    for attributes and properties.
    """

    __abstract__ = True

    @property
    def id_str(self) -> str:
        """Returns a string representation of the primary key.

        If the primary key is composite, returns a comma-separated list of key-value pairs.

        Examples
        --------
        Assuming you have a model named ``User`` with a primary key named ``id`` and
        a model named ``Sell`` with a primary key composed of ``id`` and ``product_id``:
        >>> bob = User.insert(name='Bob')
        >>> bob.id_str
        'id=1'
        >>> sell = Sell(id=1, product_id=1)
        >>> sell.id_str
        'id=1, product_id=1'
        """

        mapped = []
        for pk in self.primary_keys_full:
            value = getattr(self, pk.key)
            mapped.append(f'{pk.key}={value}' if isinstance(value, Number) or value is None else f'{pk.key}="{value}"')
        return ', '.join(mapped)

    @classproperty
    def columns(cls) -> list[str]:
        """Returns a `list` of column names."""

        return cls.__table__.columns.keys()

    @classproperty
    def string_columns(cls) -> list[str]:
        """Returns a `list` of string column names."""

        return [c.key for c in cls.__table__.columns if c.type.python_type is str]

    @classproperty
    def primary_keys_full(cls) -> tuple[Column[Any], ...]:
        """Returns the columns that form the primary key."""

        return cls.__mapper__.primary_key

    @classproperty
    def primary_keys(cls) -> list[str]:
        """Returns the names of the primary key columns."""

        return [pk.key for pk in cls.primary_keys_full]

    @classproperty
    def primary_key_name(cls) -> str:
        """Returns the primary key name of the model.

        **WARNING**

            This property can only be used if the model has a single primary key.
            If the model has a composite primary key, an `InvalidRequestError` is raised.
        """

        if len(cls.primary_keys) > 1:
            raise InvalidRequestError(f'model `{cls.__name__}` has a composite primary key')
        return cls.primary_keys[0]

    @classproperty
    def relations(cls) -> list[str]:
        """Returns a `list` of relationship names."""

        return [c.key for c in cls.__mapper__.attrs if isinstance(c, RelationshipProperty)]

    @classproperty
    def settable_relations(cls) -> list[str]:
        """Returns a `list` of settable relationship names."""

        return [r for r in cls.relations if getattr(cls, r).property.viewonly is False]

    @classproperty
    def hybrid_properties(cls) -> list[str]:
        """Returns a `list` of hybrid property names."""

        items = cls.__mapper__.all_orm_descriptors
        return [item.__name__ for item in items if isinstance(item, hybrid_property)]

    @classproperty
    def hybrid_methods_full(cls):
        """Returns a `dict` of hybrid methods."""

        items = cls.__mapper__.all_orm_descriptors
        return {item.func.__name__: item for item in items if type(item) is hybrid_method}

    @classproperty
    def hybrid_methods(cls) -> list[str]:
        """Returns a `list` of hybrid method names."""

        return list(cls.hybrid_methods_full.keys())

    @classproperty
    def filterable_attributes(cls) -> list[str]:
        """Returns a `list` of filterable attributes.

        These are all columns, relations and hybrid properties.
        """

        return cls.relations + cls.columns + cls.hybrid_properties + cls.hybrid_methods

    @classproperty
    def sortable_attributes(cls) -> list[str]:
        """Returns a `list` of sortable attributes.

        These are all columns and hybrid properties.
        """

        return cls.columns + cls.hybrid_properties

    @classproperty
    def settable_attributes(cls) -> list[str]:
        """Returns a `list` of settable attributes.

        These are all columns, settable relations and hybrid properties.
        """

        return cls.columns + cls.hybrid_properties + cls.settable_relations

    @classproperty
    def searchable_attributes(cls) -> list[str]:
        """Returns a `list` of searchable attributes.

        These are all string columns.
        """

        return cls.string_columns

    @classmethod
    def get_primary_key_filter_criteria(cls, pk: object | dict[str, object]) -> dict[str, Any]:
        """Returns a `dict` of primary key filter criteria.

        Parameters
        ----------
        pk : object | dict[str, object]
            Primary key value or dict of composite primary key values.

        Returns
        -------
        dict[str, Any]
            Primary key filter criteria.
        """
        if isinstance(pk, dict):
            return {pk_column.key: pk[pk_column.key] for pk_column in cls.primary_keys_full if pk_column.key in pk}

        return {cls.primary_key_name: pk}

    @classmethod
    def get_class_of_relation(cls, relation_name: str) -> type[Self]:
        """Gets the class of a relationship by its name.

        Parameters
        ----------
        relation_name : str
            The name of the relationship

        Examples
        --------
        Assuming you have a model named ``User`` related to a model named ``Post``
        through a relationship named ``posts``:
        >>> bob = User.insert(name='Bob')
        >>> bob.get_class_of_relation('posts')
        <class 'Post'>
        """

        return cls.__mapper__.relationships[relation_name].mapper.class_

    def __repr__(self) -> str:
        """Returns a string representation of the model.

        Representation format is ``ClassName(pk1=value1, pk2=value2, ...)``

        Examples
        --------
        Assuming you have a model named ``User`` with a primary key named ``id``:
        >>> bob = User.insert(name='Bob')
        >>> bob
        User(id=1)
        >>> users = await User.find(name__like='%John%')
        >>> users
        [User(id=1), User(id=2), ...]
        """

        return f'{self.__class__.__name__}({self.id_str})'

"""This module defines `InspectionMixin` class."""

from typing import Any

from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import DeclarativeBase, RelationshipProperty
from sqlalchemy.sql.schema import Column
from typing_extensions import Self

from .utils import classproperty


class InspectionMixin(DeclarativeBase):
    """Mixin for SQLAlchemy models to provide inspection methods
    for attributes and properties.
    """

    __abstract__ = True

    def __repr__(self) -> str:
        """Print the model in a readable format including the primary key.

        Format:
            <ClassName #PrimaryKey>

        Example:
        >>> bob = User.insert(name='Bob')
        >>> bob
        # <User #1>
        >>> users = await User.find(name__like='%John%')
        >>> users
        # [<User #1>, <User #2>, ...]
        """

        id_str = ('#' + self.id_str) if self.id_str else ''
        return f'<{self.__class__.__name__} {id_str}>'

    @classmethod
    def get_class_of_relation(cls, relation_name: str) -> type[Self]:
        """Gets the class of a relationship by its name.

        Parameters
        ----------
        relation_name : str
            The name of the relationship

        Example:
        >>> bob = User.insert(name='Bob')
        >>> bob.get_class_of_relation('posts')
        # <class 'Post'>
        """

        return cls.__mapper__.relationships[relation_name].mapper.class_

    @property
    def id_str(self) -> str:
        """Returns primary key as string.

        If there is a composite primary key, returns a hyphenated string,
        as follows: '1-2-3'.

        Example:
        >>> bob = User.insert(name='Bob')
        >>> bob.id_str
        # 1

        If there is no primary key, returns 'None'.
        """

        ids = inspect(self).identity
        if ids and len(ids) > 0:
            return '-'.join([str(x) for x in ids]) if len(ids) > 1 else str(ids[0])
        else:
            return 'None'

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

        **WARNING:**

            This property can only be used if the model has a single primary key.
            If the model has a composite primary key, an `InvalidRequestError` is raised.
        """

        if len(cls.primary_keys) > 1:
            raise InvalidRequestError(f'Model {cls.__name__} has a composite primary key.')
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

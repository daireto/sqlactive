"""This module defines `InspectionMixin` class."""

from sqlalchemy.inspection import inspect
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.orm import DeclarativeBase, RelationshipProperty

from .utils import classproperty


class InspectionMixin(DeclarativeBase):
    """Mixin for SQLAlchemy models to provide inspection methods
    for attributes and properties.
    """

    __abstract__ = True

    @property
    def id_str(self) -> str:
        """Returns primary key as string.

        If there is a composite primary key, returns a hyphenated string,
        as follows: '1-2-3'.

        Example:
        >>> bob = User.create(name='Bob')
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
        """Sequence of string key names for all columns in this collection."""

        return cls.__table__.columns.keys()

    @classproperty
    def primary_keys_full(cls):
        """Gets primary key properties for a SQLAlchemy cls.

        Taken from marshmallow_sqlalchemy.
        """

        mapper = cls.__mapper__
        return [mapper.get_property_by_column(column) for column in mapper.primary_key]

    @classproperty
    def primary_keys(cls):
        """Returns a `list` of primary key names."""

        return [pk.key for pk in cls.primary_keys_full]

    @classproperty
    def relations(cls):
        """Returns a `list` of relationship names."""

        return [c.key for c in cls.__mapper__.attrs if isinstance(c, RelationshipProperty)]

    @classproperty
    def settable_relations(cls):
        """Returns a `list` of settable relationship names."""

        return [r for r in cls.relations if getattr(cls, r).property.viewonly is False]

    @classproperty
    def hybrid_properties(cls):
        """Returns a `list` of hybrid property names."""

        items = cls.__mapper__.all_orm_descriptors
        return [item.__name__ for item in items if isinstance(item, hybrid_property)]

    @classproperty
    def hybrid_methods_full(cls):
        """Returns a `dict` of hybrid methods."""

        items = cls.__mapper__.all_orm_descriptors
        return {item.func.__name__: item for item in items if type(item) is hybrid_method}

    @classproperty
    def hybrid_methods(cls):
        """Returns a `list` of hybrid method names."""

        return list(cls.hybrid_methods_full.keys())

    @classproperty
    def filterable_attributes(cls):
        """Returns a `list` of filterable attributes.

        These are all columns, relations and hybrid properties.
        """

        return cls.relations + cls.columns + cls.hybrid_properties + cls.hybrid_methods

    @classproperty
    def sortable_attributes(cls):
        """Returns a `list` of sortable attributes.

        These are all columns and hybrid properties.
        """

        return cls.columns + cls.hybrid_properties

    @classproperty
    def settable_attributes(cls):
        """Returns a `list` of settable attributes.

        These are all columns, settable relations and hybrid properties.
        """

        return cls.columns + cls.hybrid_properties + cls.settable_relations

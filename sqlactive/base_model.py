"""This module defines ``ActiveRecordBaseModel`` class."""

from .active_record import ActiveRecordMixin
from .serialization import SerializationMixin
from .timestamp import TimestampMixin


class ActiveRecordBaseModel(
    ActiveRecordMixin, SerializationMixin, TimestampMixin
):
    """This is intended to be a base class for all models.

    Inherits from:

    - ``ActiveRecordMixin``: Provides a set of ActiveRecord-like
    helper methods for interacting with the database.
    - ``TimestampMixin``: Adds the ``created_at`` and ``updated_at``
    timestamp columns.
    - ``SerializationMixin``: Provides serialization
    and deserialization methods.

    It is recommended to define a ``BaseModel`` class that inherits
    from ``ActiveRecordBaseModel`` and use it as the base class for all
    models as shown in the following example::

        from sqlalchemy import Mapped, mapped_column
        from sqlactive import ActiveRecordBaseModel

        class BaseModel(ActiveRecordBaseModel):
            __abstract__ = True

        class User(BaseModel):
            __tablename__ = 'users'
            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str] = mapped_column(String(100))

    Overview of Active Record methods:
    >>> bob = User.insert(name='Bob')
    >>> bob
    # <User #1>
    >>> bob.name
    # Bob
    >>> User.where(name='Bob').all()
    # [<User #1>]
    >>> User.get(1)
    # <User #1>
    >>> bob.update(name='Bob2')
    >>> bob.name
    # Bob2
    >>> bob.to_dict()
    # {'id': 2, 'name': 'Bob2'}
    >>> bob.to_json()
    # '{"id": 2, "name": "Bob2"}'
    >>> bob.delete()
    >>> User.all()
    # []

    .. note::
        When defining a ``BaseModel`` class, don't forget to set
        ``__abstract__`` to ``True`` in the base class to avoid
        creating tables for the base class.
    """

    __abstract__ = True

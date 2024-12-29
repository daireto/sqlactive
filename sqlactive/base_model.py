"""This module defines `ActiveRecordBaseModel` class."""

from typing import Iterable
from sqlalchemy.orm.exc import DetachedInstanceError

from .active_record import ActiveRecordMixin
from .timestamp import TimestampMixin


class ActiveRecordBaseModel(ActiveRecordMixin, TimestampMixin):
    """This is intended to be a base class for all models.

    Inherits from `ActiveRecordMixin` class to provide a set of
    ActiveRecord-like helper methods for interacting with the database.

    It also inherits from `TimestampMixin` class which adds
    the `created_at` and `updated_at` timestamp columns.
    To customize the column names, override the `__created_at_name__`
    and `__updated_at_name__` class variables as shown in the following
    example:

    ```python
        class MyModel(ActiveRecordBaseModel):
            __created_at_name__ = 'created_at'
            __updated_at_name__ = 'updated_at'
    ```

    The `__datetime_func__` class variable can be used to override the default
    datetime function as shown in the following example:

    ```python
        from sqlalchemy.sql import func

        class MyModel(ActiveRecordBaseModel):
            __datetime_func__ = func.current_timestamp()
    ```

    It is recommended to define a `BaseModel` class that inherits from
    `ActiveRecordBaseModel` and use it as the base class for all models
    as shown in the following example:

    Usage:
    ```python
        from sqlalchemy import Mapped, mapped_column
        from sqlactive import ActiveRecordBaseModel

        class BaseModel(ActiveRecordBaseModel):
            __abstract__ = True

        class User(BaseModel):
            __tablename__ = 'users'
            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str] = mapped_column(String(100))
    ```

    This class provides a `to_dict` method which returns a dictionary
    representation of the model's data and a custom `__repr__` definition
    to print the model in a readable format including the primary key.

    Example:
    >>> bob = User.create(name='Bob')
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
    >>> bobo.to_dict()
    # {'id': 2, 'name': 'Bob2'}
    >>> bob.delete()
    >>> User.all()
    # []

    NOTE: When defining a `BaseModel` class, don't forget to set `__abstract__` to `True`
    in the base class to avoid creating tables for the base class.
    """

    __abstract__ = True

    def __repr__(self) -> str:
        """Print the model in a readable format including the primary key.

        Format:
            <ClassName #PrimaryKey>

        Example:
        >>> bob = User.create(name='Bob')
        >>> bob
        # <User #1>
        """

        id_str = ('#' + self.id_str) if self.id_str else ''
        return f'<{self.__class__.__name__} {id_str}>'

    def to_dict(self, nested: bool = False, hybrid_attributes: bool = False, exclude: list[str] | None = None) -> dict:
        """Serializes the model to a dictionary.

        Parameters
        ----------
        nested : bool, optional
            Set to `True` to include nested relationships' data, by default False.
        hybrid_attributes : bool, optional
            Set to `True` to include hybrid attributes, by default False.
        exclude : list[str] | None, optional
            Exclude specific attributes from the result, by default None.
        """

        result = dict()

        if exclude is None:
            view_cols = self.columns
        else:
            view_cols = filter(lambda e: e not in exclude, self.columns)

        for key in view_cols:
            result[key] = getattr(self, key, None)

        if hybrid_attributes:
            for key in self.hybrid_properties:
                result[key] = getattr(self, key, None)

        if nested:
            for key in self.relations:
                try:
                    obj = getattr(self, key)

                    if isinstance(obj, ActiveRecordBaseModel):
                        result[key] = obj.to_dict(hybrid_attributes=hybrid_attributes)
                    elif isinstance(obj, Iterable):
                        result[key] = [
                            o.to_dict(hybrid_attributes=hybrid_attributes)
                            for o in obj
                            if isinstance(o, ActiveRecordBaseModel)
                        ]
                except DetachedInstanceError:
                    continue

        return result

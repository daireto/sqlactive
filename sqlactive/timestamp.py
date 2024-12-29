"""This module defines `TimestampMixin` class."""

from datetime import datetime

from sqlalchemy.sql import func
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.orm import mapped_column, Mapped


class TimestampMixin:
    """Mixin that define timestamp columns.

    To customize the column names, override the `__created_at_name__`
    and `__updated_at_name__` class variables:

    ```python
        class MyModel(TimestampMixin):
            __created_at_name__ = 'created_at'
            __updated_at_name__ = 'updated_at'
    ```

    The `__datetime_func__` class variable can be used to override the
    default datetime function as shown in the following example:

    ```python
        from sqlalchemy.sql import func

        class MyModel(TimestampMixin):
            __datetime_func__ = func.current_timestamp()
    ```
    """

    __created_at_name__ = 'created_at'
    """Name of `created_at` column."""

    __updated_at_name__ = 'updated_at'
    """Name of `updated_at` column."""

    __datetime_func__ = func.now()
    """Default value for `created_at` and `updated_at` columns."""

    created_at: Mapped[datetime] = mapped_column(
        __created_at_name__,
        TIMESTAMP(timezone=False),
        default=__datetime_func__,
        nullable=False,
    )
    """Column for `created_at` timestamp."""

    updated_at: Mapped[datetime] = mapped_column(
        __updated_at_name__,
        TIMESTAMP(timezone=False),
        default=__datetime_func__,
        onupdate=__datetime_func__,
        nullable=False,
    )
    """Column for `updated_at` timestamp."""

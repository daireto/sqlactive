"""Utils for Active SQLAlchemy."""

from collections.abc import Callable
from typing import Any, Generic

from .types import T


class classproperty(Generic[T]):
    """Decorator for a Class-level property.

    Usage:
    >>> class Foo:
    ...     @classproperty
    ...     def foo(cls):
    ...         return 'foo'
    >>> Foo.foo
    'foo'
    >>> Foo().foo
    'foo'
    """

    fget: Callable[[Any], T]

    def __init__(self, func: Callable[[Any], T]) -> None:
        self.fget = func

    def __get__(self, _: object, owner_cls: type | None = None) -> T:
        return self.fget(owner_cls)

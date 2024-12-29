"""Utils for Active SQLAlchemy."""

from typing import Any, Callable, Generic, TypeVar


_T = TypeVar('_T')


class classproperty(Generic[_T]):
    """Decorator for a Class-level property.

    Usage:

    ```python
        class Foo:
            @classproperty
            def foo(cls):
                return "foo"
    ```
    >>> Foo.foo
    # foo
    >>> Foo().foo
    # foo
    """

    fget: Callable[[Any], _T]

    def __init__(self, func: Callable[[Any], _T]) -> None:
        self.fget = func

    def __get__(self, _: object, owner_cls: type | None = None) -> _T:
        return self.fget(owner_cls)

"""This module defines ``SerializationMixin`` class."""

import json
from collections.abc import Iterable
from typing import Any, overload

from sqlalchemy.orm.exc import DetachedInstanceError
from typing_extensions import Self

from sqlactive.exceptions import ModelAttributeError

from .inspection import InspectionMixin


class SerializationMixin(InspectionMixin):
    """Mixin for SQLAlchemy models to provide serialization methods."""

    __abstract__ = True

    def to_dict(
        self,
        nested: bool = False,
        hybrid_attributes: bool = False,
        exclude: list[str] | None = None,
        nested_exclude: list[str] | None = None,
    ) -> dict[str, Any]:
        """Serializes the model to a dictionary.

        Parameters
        ----------
        nested : bool, optional
            Set to ``True`` to include nested relationships,
            by default False.
        hybrid_attributes : bool, optional
            Set to ``True`` to include hybrid attributes,
            by default False.
        exclude : list[str] | None, optional
            Exclude specific attributes from the result,
            by default None.
        nested_exclude : list[str] | None, optional
            Exclude specific attributes from nested relationships,
            by default None.

        Returns
        -------
        dict[str, Any]
            Serialized model.

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
        >>> user = await User.get(id=1)
        >>> user.to_dict()
        >>> {'id': 1, 'username': 'user1', 'name': 'John', 'age': 30, ...}
        >>> user.to_dict(nested=True)
        >>> {'id': 1, 'username': 'user1', 'name': 'John', 'age': 30, 'posts': [...], ...}
        >>> user.to_dict(hybrid_attributes=True)
        >>> {'id': 1, 'username': 'user1', 'name': 'John', 'age': 30, 'posts_count': 3, ...}
        >>> user.to_dict(exclude=['id', 'username'])
        >>> {'name': 'John', 'age': 30, ...}
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

                    if isinstance(obj, SerializationMixin):
                        result[key] = obj.to_dict(
                            hybrid_attributes=hybrid_attributes,
                            exclude=nested_exclude,
                        )
                    elif isinstance(obj, Iterable):
                        result[key] = [
                            o.to_dict(
                                hybrid_attributes=hybrid_attributes,
                                exclude=nested_exclude,
                            )
                            for o in obj
                            if isinstance(o, SerializationMixin)
                        ]
                except DetachedInstanceError:
                    continue

        return result

    def to_json(
        self,
        nested: bool = False,
        hybrid_attributes: bool = False,
        exclude: list[str] | None = None,
        nested_exclude: list[str] | None = None,
        ensure_ascii: bool = False,
        indent: int | str | None = None,
        sort_keys: bool = False,
    ) -> str:
        """Serializes the model to JSON.

        Calls the ``to_dict()`` method and dumps it to JSON.

        Parameters
        ----------
        nested : bool, optional
            Set to ``True`` to include nested relationships' data,
            by default False.
        hybrid_attributes : bool, optional
            Set to ``True`` to include hybrid attributes,
            by default False.
        exclude : list[str] | None, optional
            Exclude specific attributes from the result,
            by default None.
        nested_exclude : list[str] | None, optional
            Exclude specific attributes from nested relationships,
            by default None.
        ensure_ascii : bool, optional
            If False, then the return value can contain non-ASCII
            characters if they appear in strings contained in obj.
            Otherwise, all such characters are escaped in JSON strings,
            by default False.
        indent : int | str | None, optional
            If indent is a non-negative integer, then JSON array
            elements and object members will be pretty-printed with
            that indent level. An indent level of 0 will only insert
            newlines. ``None`` is the most compact representation,
            by default None.
        sort_keys : bool, optional
            Sort dictionary keys, by default False.

        Returns
        -------
        str
            Serialized model.

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
        >>> user = await User.get(id=1)
        >>> user.to_json()
        {"id": 1, "username": "user1", "name": "John", "age": 30, ...}
        >>> user.to_json(nested=True)
        {"id": 1, "username": "user1", "name": "John", "age": 30, "posts": [...], ...}
        >>> user.to_json(hybrid_attributes=True)
        {"id": 1, "username": "user1", "name": "John", "age": 30, "posts_count": 3, ...}
        >>> user.to_json(exclude=['id', 'username'])
        {"name": "John", "age": 30, ...}
        """
        dumped_model = self.to_dict(
            nested=nested,
            hybrid_attributes=hybrid_attributes,
            exclude=exclude,
            nested_exclude=nested_exclude,
        )
        return json.dumps(
            obj=dumped_model,
            ensure_ascii=ensure_ascii,
            indent=indent,
            sort_keys=sort_keys,
            default=str,
        )

    @overload
    @classmethod
    def from_dict(
        cls,
        data: dict,
        exclude: list[str] | None = None,
        nested_exclude: list[str] | None = None,
    ) -> Self: ...

    @overload
    @classmethod
    def from_dict(
        cls,
        data: list,
        exclude: list[str] | None = None,
        nested_exclude: list[str] | None = None,
    ) -> list[Self]: ...

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any] | list[dict[str, Any]],
        exclude: list[str] | None = None,
        nested_exclude: list[str] | None = None,
    ) -> Self | list[Self]:
        """Deserializes a dictionary to the model.

        Sets the attributes of the model with the values
        of the dictionary.

        Parameters
        ----------
        data : dict[str, Any] | list[dict[str, Any]]
            Data to deserialize.
        exclude : list[str] | None, optional
            Exclude specific keys from the dictionary, by default None.
        nested_exclude : list[str] | None, optional
            Exclude specific attributes from nested relationships,
            by default None.

        Returns
        -------
        Self
            Deserialized model.
        list[Self]
            Deserialized models.

        Raises
        ------
        ModelAttributeError
            If attribute does not exist.

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
        >>> user = await User.from_dict({'name': 'John', 'age': 30})
        >>> user.to_dict()
        {'name': 'John', 'age': 30, ...}
        >>> users = await User.from_dict([{'name': 'John', 'age': 30}, {'name': 'Jane', 'age': 25}])
        >>> users[0].to_dict()
        {'name': 'John', 'age': 30, ...}
        >>> users[1].to_dict()
        {'name': 'Jane', 'age': 25, ...}
        """
        if isinstance(data, list):
            return [cls.from_dict(d, exclude, nested_exclude) for d in data]

        obj = cls()
        for name in data.keys():
            if exclude is not None and name in exclude:
                continue

            if name in obj.hybrid_properties:
                continue

            if name in obj.relations:
                relation_class = cls.get_class_of_relation(name)
                setattr(
                    obj,
                    name,
                    relation_class.from_dict(
                        data[name], exclude=nested_exclude
                    ),
                )
                continue

            if name in obj.columns:
                setattr(obj, name, data[name])
            else:
                raise ModelAttributeError(name, cls.__name__)

        return obj

    @classmethod
    def from_json(
        cls,
        json_string: str,
        exclude: list[str] | None = None,
        nested_exclude: list[str] | None = None,
    ) -> Any:
        """Deserializes a JSON string to the model.

        Loads the JSON string and sets the attributes of the model
        with the values of the JSON object using the ``from_dict``
        method.

        Parameters
        ----------
        json_string : str
            JSON string.
        exclude : list[str] | None, optional
            Exclude specific keys from the dictionary, by default None.
        nested_exclude : list[str] | None, optional
            Exclude specific attributes from nested relationships,
            by default None.

        Returns
        -------
        Any
            Deserialized model or models.

        Raises
        ------
        ModelAttributeError
            If attribute does not exist.

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
        >>> user = await User.from_json('{"name": "John", "age": 30}')
        >>> user.to_dict()
        {'name': 'John', 'age': 30, ...}
        >>> users = await User.from_json('[{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]')
        >>> users[0].to_dict()
        {'name': 'John', 'age': 30, ...}
        >>> users[1].to_dict()
        {'name': 'Jane', 'age': 25, ...}
        """
        data = json.loads(json_string)
        return cls.from_dict(data, exclude, nested_exclude)

# Serialization Mixin

The `SerializationMixin` class provides methods for serializing and deserializing
SQLAlchemy models.

It uses the functionality of the [`Inspection Mixin`](inspection-mixin.md).

???+ info

    The examples below assume the following models:

    ```python
    from sqlalchemy import ForeignKey, String
    from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
    from sqlalchemy.orm import Mapped, mapped_column, relationship

    from sqlactive.base_model import ActiveRecordBaseModel


    class BaseModel(ActiveRecordBaseModel):
        __abstract__ = True


    class User(BaseModel):
        __tablename__ = 'users'

        id: Mapped[int] = mapped_column(
            primary_key=True, autoincrement=True, index=True
        )
        username: Mapped[str] = mapped_column(
            String(18), nullable=False, unique=True
        )
        name: Mapped[str] = mapped_column(String(50), nullable=False)
        age: Mapped[int] = mapped_column(nullable=False)

        posts: Mapped[list['Post']] = relationship(back_populates='user')
        comments: Mapped[list['Comment']] = relationship(back_populates='user')

        @hybrid_property
        def is_adult(self) -> int:
            return self.age > 18

        @hybrid_method
        def older_than(self, other: 'User') -> bool:
            return self.age > other.age


    class Post(BaseModel):
        __tablename__ = 'posts'

        id: Mapped[int] = mapped_column(
            primary_key=True, autoincrement=True, index=True
        )
        title: Mapped[str] = mapped_column(String(100), nullable=False)
        body: Mapped[str] = mapped_column(nullable=False)
        rating: Mapped[int] = mapped_column(nullable=False)
        user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))

        user: Mapped['User'] = relationship(back_populates='posts')
        comments: Mapped[list['Comment']] = relationship(back_populates='post')


    class Comment(BaseModel):
        __tablename__ = 'comments'

        id: Mapped[int] = mapped_column(
            primary_key=True, autoincrement=True, index=True
        )
        body: Mapped[str] = mapped_column(nullable=False)
        post_id: Mapped[int] = mapped_column(ForeignKey('posts.id'))
        user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))

        post: Mapped['Post'] = relationship(back_populates='comments')
        user: Mapped['User'] = relationship(back_populates='comments')


    class Product(BaseModel):
        __tablename__ = 'products'

        id: Mapped[int] = mapped_column(
            primary_key=True, autoincrement=True, index=True
        )
        name: Mapped[str] = mapped_column(String(100), nullable=False)
        description: Mapped[str] = mapped_column(String(100), nullable=False)
        price: Mapped[float] = mapped_column(nullable=False)

        sells: Mapped[list['Sell']] = relationship(
            back_populates='product', viewonly=True
        )


    class Sell(BaseModel):
        __tablename__ = 'sells'

        id: Mapped[int] = mapped_column(primary_key=True)
        product_id: Mapped[int] = mapped_column(
            ForeignKey('products.id'), primary_key=True
        )
        quantity: Mapped[int] = mapped_column(nullable=False)

        product: Mapped['Product'] = relationship(back_populates='sells')
    ```

## API Reference

### Serialization

#### to_dict

```python
@classmethod
def to_dict(
    nested: bool = False,
    hybrid_attributes: bool = False,
    exclude: list[str] | None = None,
    nested_exclude: list[str] | None = None,
) -> dict[str, Any]
```

> Serialize the model to a dictionary.

> **Parameters**

> - `nested`: Set to `True` to include nested relationships (default: `False`).
> - `hybrid_attributes`: Set to `True` to include hybrid attributes
> (default: `False`).
> - `exclude`: Exclude specific attributes from the result (default: `None`).
> - `nested_exclude`: Exclude specific attributes from nested relationships
> (default: `None`).

> **Returns**

> - `dict[str, Any]`: Serialized model.

> **Examples**

> ```pycon
> >>> user = await User.get(id=1)
> >>> user.to_dict()
> {'id': 1, 'username': 'user1', 'name': 'John', 'age': 30, ...}
> >>> user.to_dict(nested=True)
> {'id': 1, 'username': 'user1', 'name': 'John', 'age': 30, 'posts': [...], ...}
> >>> user.to_dict(hybrid_attributes=True)
> {'id': 1, 'username': 'user1', 'name': 'John', 'age': 30, 'posts_count': 3, ...}
> >>> user.to_dict(exclude=['id', 'username'])
> {'name': 'John', 'age': 30, ...}
> ```

#### to_json

```python
@classmethod
def to_json(
    nested: bool = False,
    hybrid_attributes: bool = False,
    exclude: list[str] | None = None,
    nested_exclude: list[str] | None = None,
    ensure_ascii: bool = False,
    indent: int | str | None = None,
    sort_keys: bool = False
) -> str
```

> Serialize the model to JSON.

> Calls the [`to_dict()`](#to_dict) method and dumps it to JSON.

> **Parameters**

> - `nested`: Set to `True` to include nested relationships (default: `False`).
> - `hybrid_attributes`: Set to `True` to include hybrid attributes
> (default: `False`).
> - `exclude`: Exclude specific attributes from the result (default: `None`).
> - `nested_exclude`: Exclude specific attributes from nested relationships
> (default: `None`).
> - `ensure_ascii`: If False, then the return value can contain non-ASCII
> characters if they appear in strings contained in obj. Otherwise, all
> such characters are escaped in JSON strings (default: `False`).
> - `indent`: If indent is a non-negative integer, then JSON array elements
> and object members will be pretty-printed with that indent level. An indent
> level of 0 will only insert newlines. `None` is the most compact
> representation (default: `None`).
> - `sort_keys`: Sort dictionary keys (default: `False`).

> **Returns**

> - `str`: Serialized model.

> **Examples**

> ```pycon
> >>> user = await User.get(id=1)
> >>> user.to_json()
> {"id": 1, "username": "user1", "name": "John", "age": 30, ...}
> >>> user.to_json(nested=True)
> {"id": 1, "username": "user1", "name": "John", "age": 30, "posts": [...], ...}
> >>> user.to_json(hybrid_attributes=True)
> {"id": 1, "username": "user1", "name": "John", "age": 30, "posts_count": 3, ...}
> >>> user.to_json(exclude=['id', 'username'])
> {"name": "John", "age": 30, ...}
> ```

### Deserialization

#### from_dict

```python
@classmethod
def from_dict(
    data: dict[str, Any] | list[dict[str, Any]],
    exclude: list[str] | None = None,
    nested_exclude: list[str] | None = None
) -> Self | list[Self]
```

> Deserialize a dictionary to the model.

> Sets the attributes of the model with the values of the dictionary.

> **Parameters**

> - `data`: Data to deserialize.
> - `exclude`: Exclude specific keys from the dictionary (default: `None`).
> - `nested_exclude`: Exclude specific attributes from nested relationships
> (default: `None`).

> **Returns**

> - `Self`: Deserialized model.
> - `list[Self]`: Deserialized models.

> **Raises**

> - `ModelAttributeError`: If attribute does not exist.

> **Examples**

> ```pycon
> >>> user = await User.from_dict({'name': 'John', 'age': 30})
> >>> user.to_dict()
> {'name': 'John', 'age': 30, ...}
> >>> users = await User.from_dict(
> ...     [{'name': 'John', 'age': 30}, {'name': 'Jane', 'age': 25}]
> ... )
> >>> users[0].to_dict()
> {'name': 'John', 'age': 30, ...}
> >>> users[1].to_dict()
> {'name': 'Jane', 'age': 25, ...}
> ```

#### from_json

```python
@classmethod
def from_json(
    json_string: str,
    exclude: list[str] | None = None,
    nested_exclude: list[str] | None = None
) -> Any
```

> Deserialize a JSON string to the model.

> Loads the JSON string and sets the attributes of the model with the values
> of the JSON object using the `from_dict` method.

> **Parameters**

> - `json_string`: JSON string.
> - `exclude`: Exclude specific keys from the dictionary (default: `None`).
> - `nested_exclude`: Exclude specific attributes from nested relationships
> (default: `None`).

> **Returns**

> - `Any`: Deserialized model or models.

> **Raises**

> - `ModelAttributeError`: If attribute does not exist.

> **Examples**

> ```pycon
> >>> user = await User.from_json('{"name": "John", "age": 30}')
> >>> user.to_dict()
> {'name': 'John', 'age': 30, ...}
> >>> users = await User.from_json(
> ...     '[{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]'
> ... )
> >>> users[0].to_dict()
> {'name': 'John', 'age': 30, ...}
> >>> users[1].to_dict()
> {'name': 'Jane', 'age': 25, ...}
> ```

# Inspection Mixin

The `InspectionMixin` class provides attributes and properties inspection
functionality for SQLAlchemy models.

???+ note

    This mixin is intended to extend the functionality of the
    [`Smart Queries`](smart-query-mixin.md) and
    [`Serialization`](serialization-mixin.md) mixins.
    It is not intended to be used on its own.

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

### Properties

#### id_str
```python
@property
def id_str() -> str
```

> Returns a string representation of the primary key.

> If the primary key is composite, returns a comma-separated list of
> key-value pairs.

> **Examples**

> ```python
> >>> bob = User.insert(name='Bob')
> >>> bob.id_str
> 'id=1'
> >>> sell = Sell(id=1, product_id=1)
> >>> sell.id_str
> 'id=1, product_id=1'
> ```

### Class Properties

#### columns
```python
@classproperty
def columns() -> list[str]
```

> Returns a list of column names.

> **Examples**

> ```python
> >>> User.columns
> ['id', 'username', 'name', 'age', 'created_at', 'updated_at']
> ```

#### string_columns
```python
@classproperty
def string_columns() -> list[str]
```

> Returns a list of string column names.

> **Examples**

> ```python
> >>> User.string_columns
> ['username', 'name']
> ```

#### primary_keys_full
```python
@classproperty
def primary_keys_full() -> tuple[Column[Any], ...]
```

> Returns the columns that form the primary key.

> **Examples**

> ```python
> >>> User.primary_keys_full
> (Column('id', Integer(), table=<users>, primary_key=True, nullable=False),)
> ```

#### primary_keys
```python
@classproperty
def primary_keys() -> list[str]
```

> Returns the names of the primary key columns.

> **Examples**

> ```python
> >>> User.primary_keys
> ['id']
> ```

#### primary_key_name
```python
@classproperty
def primary_key_name() -> str
```

> Returns the primary key name of the model.

> ???+ warning
>
>     This property can only be used if the model has a single primary key.
>     If the model has a composite primary key, an `CompositePrimaryKeyError`
>     is raised.

> **Examples**

> ```python
> >>> User.primary_key_name
> 'id'
> >>> Sell.primary_key_name
> Traceback (most recent call last):
> ...
> CompositePrimaryKeyError: model 'Sell' has a composite primary key
> ```

#### relations
```python
@classproperty
def relations() -> list[str]
```

> Returns a list of relationship names.

> **Examples**

> ```python
> >>> User.relations
> ['posts', 'comments']
> ```

#### settable_relations
```python
@classproperty
def settable_relations() -> list[str]
```

> Returns a list of settable (not viewonly) relationship names.

> **Examples**

> ```python
> >>> User.settable_relations
> ['posts', 'comments']
> >>> Product.settable_relations
> []
> ```

#### hybrid_properties
```python
@classproperty
def hybrid_properties() -> list[str]
```

> Returns a list of hybrid property names.

> **Examples**

> ```python
> >>> User.hybrid_properties
> ['is_adult']
> ```

#### hybrid_methods_full
```python
@classproperty
def hybrid_methods_full() -> dict[str, hybrid_method[..., Any]]
```

> Returns a dict of hybrid methods.

> **Examples**

> ```python
> >>> User.hybrid_methods_full
> {'older_than': hybrid_method(...)}
> ```

#### hybrid_methods
```python
@classproperty
def hybrid_methods() -> list[str]
```

> Returns a list of hybrid method names.

> **Examples**

> ```python
> >>> User.hybrid_methods
> ['older_than']
> ```

#### filterable_attributes
```python
@classproperty
def filterable_attributes() -> list[str]
```

> Returns a list of filterable attributes.

> These are all columns, relations, hybrid properties and hybrid methods.

> **Examples**

> ```python
> >>> User.filterable_attributes
> >>> ['id', 'username', 'name', 'age', 'created_at', 'updated_at', 'posts', 'comments', 'is_adult', 'older_than']
> ```

#### sortable_attributes
```python
@classproperty
def sortable_attributes() -> list[str]
```

> Returns a list of sortable attributes.

> These are all columns and hybrid properties.

> **Examples**

> ```python
> >>> User.sortable_attributes
> ['id', 'username', 'name', 'age', 'created_at', 'updated_at', 'is_adult']
> ```

#### settable_attributes
```python
@classproperty
def settable_attributes() -> list[str]
```

> Returns a list of settable attributes.

> These are all columns, settable relations and hybrid properties.

> **Examples**

> ```python
> >>> User.settable_attributes
> ['username', 'name', 'age', 'created_at', 'updated_at', 'posts', 'comments', 'is_adult']
> ```

#### searchable_attributes
```python
@classproperty
def searchable_attributes() -> list[str]
```

> Returns a list of searchable attributes.

> These are all string columns.

> **Examples**

> ```python
> >>> User.searchable_attributes
> ['username', 'name']
> ```

### Instance Methods

#### __repr__
```python
def __repr__() -> str
```

> Returns a string representation of the model.

> Representation format is `ClassName(pk1=value1, pk2=value2, ...)`

> **Examples**

> ```python
> >>> user = await User.get(id=1)
> >>> user
> User(id=1)
> >>> users = await User.find(name__endswith='Doe').all()
> >>> users
> [User(id=1), User(id=2)]
> ```

### Class Methods

#### get_class_of_relation
```python
@classmethod
def get_class_of_relation(relation_name: str) -> type[Self]
```

> Gets the class of a relationship by its name.

> **Parameters**

> - `relation_name`: The name of the relationship.

> **Returns**

> - `type[Self]`: The class of the relationship.

> **Raises**

> - `RelationError`: If the relation is not found.

> **Examples**

> ```python
> >>> User.get_class_of_relation('posts')
> <class 'Post'>
> >>> User.get_class_of_relation('comments')
> <class 'Comment'>
> >>> User.get_class_of_relation('sells')
> Traceback (most recent call last):
>     ...
> RelationError: no such relation: 'sells' in model 'User'
> ```

# Inspection Mixin

The `InspectionMixin` class provides attributes and properties inspection functionality for SQLAlchemy models.

???+ info

    This mixin is intended to extend the functionality of the
    [`Smart Queries`](smart-query-mixin.md) and [`Serialization`](serialization-mixin.md) mixins.
    It is not intended to be used on its own.

## API Reference

### Instance Methods

#### __repr__
```python
def __repr__(self) -> str
```

> Prints the model in a readable format including the primary key.

> Format:
> ```
> <ClassName #PrimaryKey>
> ```

> **Example:**

> ```python
> user = await User.get(id=1)
> user
> # <User #1>
>
> users = await User.find(username__endswith='Doe').all()
> users
> # [<User #1>, <User #2>]
> ```

### Class Methods

#### get_class_of_relation
```python
@classmethod
def get_class_of_relation(relation_name: str) -> type[Self]
```

> Gets the class of a relationship by its name.

> **Parameters:**

> - `relation_name`: The name of the relationship.

> **Returns:**

> - `type`: The class of the relationship.

> **Example:**

> ```python
> user = await User.get(id=1)
> user.get_class_of_relation('posts')
> # <class 'Post'>
> ```

### Properties

#### id_str
```python
@property
def id_str() -> str
```

> Returns primary key as string.

> If there is a composite primary key, returns a hyphenated string,
> as follows: `'1-2-3'`.

> If there is no primary key, returns `'None'`.

> **Example:**

> ```python
> bob = User.insert(name='Bob')
> bob.id_str  # 1
> ```

### Class Properties

#### columns
```python
@classproperty
def columns() -> list[str]
```

> Sequence of string key names for all columns in this collection.

> **Example:**

> ```python
> User.columns
> # ['id', 'username', 'name', 'age', 'created_at', 'updated_at']
> ```

#### primary_keys_full
```python
@classproperty
def primary_keys_full() -> tuple[Column[Any], ...]
```

> Returns the columns that form the primary key.

> **Example:**

> ```python
> User.primary_keys_full
> # (<sqlalchemy.sql.schema.Column 'id'>,)
> ```

#### primary_keys
```python
@classproperty
def primary_keys() -> list[str]
```

> Returns the names of the primary key columns.

> **Example:**

> ```python
> User.primary_keys
> # ['id']
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
>     If the model has a composite primary key, an `InvalidRequestError` is raised.

> **Example:**

> ```python
> User.primary_key_name
> # 'id'
> ```

#### relations
```python
@classproperty
def relations() -> list[str]
```

> Returns a `list` of relationship names.

> **Example:**

> ```python
> User.relations
> # ['posts', 'comments']
> ```

#### settable_relations
```python
@classproperty
def settable_relations() -> list[str]
```

> Returns a `list` of settable relationship names.

> **Example:**

> ```python
> User.settable_relations
> # ['posts', 'comments']
> ```

#### hybrid_properties
```python
@classproperty
def hybrid_properties() -> list[str]
```

> Returns a `list` of hybrid property names.

> **Example:**

> ```python
> User.hybrid_properties
> # ['is_adult']
> ```

#### hybrid_methods_full
```python
@classproperty
def hybrid_methods_full() -> dict[str, InstrumentedAttribute]
```

> Returns a `dict` of hybrid methods.

> **Example:**

> ```python
> User.hybrid_methods_full
> # {'is_adult': <sqlalchemy.orm.attributes.InstrumentedAttribute 'is_adult'>}
> ```

#### hybrid_methods
```python
@classproperty
def hybrid_methods() -> list[str]
```

> Returns a `list` of hybrid method names.

> **Example:**

> ```python
> User.hybrid_methods
> # ['is_adult']
> ```

#### filterable_attributes
```python
@classproperty
def filterable_attributes() -> list[str]
```

> Returns a `list` of filterable attributes.

> These are all columns, relations and hybrid properties.

> **Example:**

> ```python
> User.filterable_attributes
> # ['id', 'username', 'name', 'age', 'created_at', 'updated_at', 'posts', ...]
> ```

#### sortable_attributes
```python
@classproperty
def sortable_attributes() -> list[str]
```

> Returns a `list` of sortable attributes.

> These are all columns and hybrid properties.

> **Example:**

> ```python
> User.sortable_attributes
> # ['id', 'username', 'name', 'age', 'created_at', 'updated_at', 'is_adult']
> ```

#### settable_attributes
```python
@classproperty
def settable_attributes() -> list[str]
```

> Returns a `list` of settable attributes.

> These are all columns, settable relations and hybrid properties.

> **Example:**

> ```python
> User.settable_attributes
> # ['id', 'username', 'name', 'age', 'created_at', 'updated_at', 'posts', ...]
> ```

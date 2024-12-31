# SerializationMixin

The `SerializationMixin` class provides methods for serializing and deserializing
SQLAlchemy models.

It uses the [`InspectionMixin`](inspection_mixin.md) class functionality.

**Table of Contents**

- [SerializationMixin](#serializationmixin)
  - [Serialization](#serialization)
    - [to\_dict](#to_dict)
    - [to\_json](#to_json)
  - [Deserialization](#deserialization)
    - [from\_dict](#from_dict)
    - [from\_json](#from_json)

## Serialization

### to_dict
```python
def to_dict(nested: bool = False, hybrid_attributes: bool = False, exclude: list[str] | None = None)
```

> Serializes the model to a dictionary.

> **Parameters:**

> - `nested`: Set to `True` to include nested relationships' data, by default False.
> - `hybrid_attributes`: Set to `True` to include hybrid attributes, by default False.
> - `exclude`: Exclude specific attributes from the result, by default None.

> **Returns:**

> - `dict`: Serialized model.

> **Example:**

> ```python
> user = await User.get(id=1)
> user.to_dict()
> # {'id': 1, 'username': 'user1', 'name': 'John', 'age': 30, ...}
> user.to_dict(nested=True)
> # {'id': 1, 'username': 'user1', 'name': 'John', 'age': 30, 'posts': [...], ...}
> user.to_dict(hybrid_attributes=True)
> # {'id': 1, 'username': 'user1', 'name': 'John', 'age': 30, 'posts_count': 3, ...}
> user.to_dict(exclude=['id', 'username'])
> # {'name': 'John', 'age': 30, ...}
> ```

### to_json
```python
def to_json(nested: bool = False, hybrid_attributes: bool = False, exclude: list[str] | None = None, ensure_ascii: bool = False, indent: int | str | None = None, sort_keys: bool = False)
```

> Serializes the model to JSON.

> Calls the `Self.to_dict` method and dumps it with `json.dumps`.

> **Parameters:**

> - `nested`: Set to `True` to include nested relationships' data, by default False.
> - `hybrid_attributes`: Set to `True` to include hybrid attributes, by default False.
> - `exclude`: Exclude specific attributes from the result, by default None.
> - `ensure_ascii`: If False, then the return value can contain non-ASCII characters if they appear in strings contained in obj. Otherwise, all such characters are escaped in JSON strings, by default False.
> - `indent`: If indent is a non-negative integer, then JSON array elements and object members will be pretty-printed with that indent level. An indent level of 0 will only insert newlines. `None` is the most compact representation, by default None.
> - `sort_keys`: Sort dictionary keys, by default False.

> **Returns:**

> - `str`: Serialized model.

> **Example:**

> ```python
> user = await User.get(id=1)
> user.to_json()
> # {"id": 1, "username": "user1", "name": "John", "age": 30, ...}
> user.to_json(nested=True)
> # {"id": 1, "username": "user1", "name": "John", "age": 30, "posts": [...], ...}
> user.to_json(hybrid_attributes=True)
> # {"id": 1, "username": "user1", "name": "John", "age": 30, "posts_count": 3, ...}
> user.to_json(exclude=['id', 'username'])
> # {"name": "John", "age": 30, ...}
> ```

## Deserialization

### from_dict
```python
def from_dict(data: dict | list, exclude: list[str] | None = None)
```

> Deserializes a dictionary to the model.

> Sets the attributes of the model with the values of the dictionary.

> **Parameters:**

> - `data`: Data to deserialize.
> - `exclude`: Exclude specific keys from the dictionary, by default None.

> **Returns:**

> - `Self | list[Self]`: Deserialized model or models.

> **Raises:**

> - `TypeError`: If the data is not a dictionary or list of dictionaries.
> - `KeyError`: If attribute doesn't exist.

> **Example:**

> ```python
> user = await User.from_dict({'name': 'John', 'age': 30})
> user.to_dict()
> # {'name': 'John', 'age': 30, ...}
> users = await User.from_dict([{'name': 'John', 'age': 30}, {'name': 'Jane', 'age': 25}])
> users[0].to_dict()
> # {'name': 'John', 'age': 30, ...}
> users[1].to_dict()
> # {'name': 'Jane', 'age': 25, ...}
> ```

### from_json
```python
def from_json(json_string: str, exclude: list[str] | None = None)
```

> Deserializes a JSON string to the model.

> Calls the `json.loads` method and sets the attributes of the model
> with the values of the JSON object using the `from_dict` method.

> **Parameters:**

> - `json_string`: JSON string.
> - `exclude`: Exclude specific keys from the dictionary, by default None.

> **Returns:**

> - `Self | list[Self]`: Deserialized model or models.

> **Example:**

> ```python
> user = await User.from_json('{"name": "John", "age": 30}')
> user.to_dict()
> # {'name': 'John', 'age': 30, ...}
> users = await User.from_json('[{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]')
> users[0].to_dict()
> # {'name': 'John', 'age': 30, ...}
> users[1].to_dict()
> # {'name': 'Jane', 'age': 25, ...}
> ```

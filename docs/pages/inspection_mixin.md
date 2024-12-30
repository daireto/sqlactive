# InspectionMixin

The `InspectionMixin` class provides attributes and properties inspection functionality for SQLAlchemy models.

!!! info

    This mixin is intended to extend the functionality of the [`SmartQueryMixin`](smart_query_mixin.md).
    It is not intended to be used on its own.

**Table of Contents**

- [InspectionMixin](#inspectionmixin)
  - [Properties](#properties)
    - [id\_str](#id_str)
    - [columns](#columns)
    - [primary\_keys\_full](#primary_keys_full)
    - [primary\_keys](#primary_keys)
    - [relations](#relations)
    - [settable\_relations](#settable_relations)
    - [hybrid\_properties](#hybrid_properties)
    - [hybrid\_methods\_full](#hybrid_methods_full)
    - [hybrid\_methods](#hybrid_methods)
    - [filterable\_attributes](#filterable_attributes)
    - [sortable\_attributes](#sortable_attributes)
    - [settable\_attributes](#settable_attributes)

## Properties

### id_str
> Returns primary key as string.

> If there is a composite primary key, returns a hyphenated string,
> as follows: '1-2-3'.

> ```python
> bob = User.create(name='Bob')
> print(bob.id_str)
> # 1
> ```

### columns
> Sequence of string key names for all columns in this collection.

> ```python
> print(User.columns)
> # ['id', 'username', 'name', 'age', 'created_at', 'updated_at']
> ```

### primary_keys_full
> Gets primary key properties for a SQLAlchemy cls.

> Taken from marshmallow_sqlalchemy.

> ```python
> print(User.primary_keys_full)
> # [<sqlalchemy.orm.attributes.InstrumentedAttribute 'id'>]
> ```

### primary_keys
> Returns a `list` of primary key names.

> ```python
> print(User.primary_keys)
> # ['id']
> ```

### relations
> Returns a `list` of relationship names.

> ```python
> print(User.relations)
> # ['posts', 'comments']
> ```

### settable_relations
> Returns a `list` of settable relationship names.

> ```python
> print(User.settable_relations)
> # ['posts', 'comments']
> ```

### hybrid_properties
> Returns a `list` of hybrid property names.

> ```python
> print(User.hybrid_properties)
> # ['is_adult']
> ```

### hybrid_methods_full
> Returns a `dict` of hybrid methods.

> ```python
> print(User.hybrid_methods_full)
> # {'is_adult': <sqlalchemy.orm.attributes.InstrumentedAttribute 'is_adult'>}
> ```

### hybrid_methods
> Returns a `list` of hybrid method names.

> ```python
> print(User.hybrid_methods)
> # ['is_adult']
> ```

### filterable_attributes
> Returns a `list` of filterable attributes.

> These are all columns, relations and hybrid properties.

> ```python
> print(User.filterable_attributes)
> # ['id', 'username', 'name', 'age', 'created_at', 'updated_at', 'posts', 'comments', 'is_adult']
> ```

### sortable_attributes
> Returns a `list` of sortable attributes.

> These are all columns and hybrid properties.

> ```python
> print(User.sortable_attributes)
> # ['id', 'username', 'name', 'age', 'created_at', 'updated_at', 'is_adult']
> ```

### settable_attributes
> Returns a `list` of settable attributes.

> These are all columns, settable relations and hybrid properties.

> ```python
> print(User.settable_attributes)
> # ['id', 'username', 'name', 'age', 'created_at', 'updated_at', 'posts', 'comments', 'is_adult']
> ```

# ActiveRecordMixin Documentation

The `ActiveRecordMixin` class provides ActiveRecord-style functionality
for SQLAlchemy models, allowing for more intuitive and chainable database
operations with async/await support.

It uses the [`SmartQueryMixin`](/docs/SMART_QUERY.md) class functionality.

Check the [API Reference](/docs/ACTIVE_RECORD_API.md) for the full list of
available methods.

<!-- omit in toc -->
## Table of Contents
- [ActiveRecordMixin Documentation](#activerecordmixin-documentation)
  - [Usage](#usage)
  - [Core Features](#core-features)
    - [Creation, Updating, and Deletion](#creation-updating-and-deletion)
      - [Creating Records](#creating-records)
      - [Updating Records](#updating-records)
      - [Deleting Records](#deleting-records)
    - [Querying](#querying)
      - [Basic Queries](#basic-queries)
      - [Filtering](#filtering)
      - [Sorting and Pagination](#sorting-and-pagination)
    - [Eager Loading](#eager-loading)
      - [Join Loading](#join-loading)
      - [Subquery Loading](#subquery-loading)
      - [Complex Schema Loading](#complex-schema-loading)
    - [Smart Queries](#smart-queries)
  - [Important Notes](#important-notes)
  - [Error Handling](#error-handling)
  - [API Reference](#api-reference)

## Usage

To use the `ActiveRecordMixin`, create a base model class that inherits from it
and set the `__abstract__` attribute to `True`:

```python
from sqlalchemy import Mapped, mapped_column
from sqlactive import ActiveRecordMixin

class BaseModel(ActiveRecordMixin):
    __abstract__ = True

class User(BaseModel):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
```

## Core Features

### Creation, Updating, and Deletion

#### Creating Records

```python
# Create a single record
bob = await User.create(name='Bob')

# Alternative creation methods
bob = await User.insert(name='Bob')  # Synonym for create
bob = await User.add(name='Bob')     # Synonym for create

# Create multiple records
users = [User(name='Alice'), User(name='Bob')]
await User.create_all(users)
```

#### Updating Records

```python
# Update a single record
await user.update(name='Bob2')
await user.edit(name='Bob2')  # Synonym for update

# Update multiple records
users = await User.where(age=25).all()
for user in users:
    user.name = f"{user.name} Jr."
await User.update_all(users)
```

#### Deleting Records

```python
# Delete a single record
await user.delete()
await user.remove()  # Synonym for delete

# Delete multiple records
users = await User.where(age=25).all()
await User.delete_all(users)

# Delete by primary keys
await User.destroy(1, 2, 3)  # Deletes users with IDs 1, 2, and 3
```

### Querying

#### Basic Queries

```python
# Get all records
users = await User.all()
users = await User.fetch_all()  # Synonym for all
users = await User.to_list()    # Synonym for all

# Get first record
user = await User.first()

# Get one record
user = await User.one()                # Raises if no result found
user = await User.one_or_none()        # Returns None if no result found
user = await User.fetch_one()          # Synonym for one
user = await User.fetch_one_or_none()  # Synonym for one_or_none
```

#### Filtering

The mixin supports both Django-like syntax and SQLAlchemy syntax for filtering:

```python
# Django-like syntax
users = await User.filter(name__like='%John%').all()
users = await User.filter(name__like='%John%', age=30).all()

# SQLAlchemy syntax
users = await User.filter(User.name == 'John Doe').all()

# Mixed syntax
users = await User.filter(User.age == 30, name__like='%John%').all()

# Alternative filter methods
users = await User.where(name__like='%John%').all()  # Synonym for filter
users = await User.find(name__like='%John%').all()   # Synonym for filter

# Find one record
user = await User.find_one(name__like='%John%', age=30)  # Raises if not found
user = await User.find_one_or_none(name__like='%John%')  # Returns None if not found
```

#### Sorting and Pagination

```python
from sqlalchemy.sql import desc

# Sorting (Django-like syntax)
users = await User.order_by('-created_at').all()  # Descending order
users = await User.sort('-created_at').all()      # Synonym for order_by

# Sorting (SQLAlchemy syntax)
users = await User.order_by(User.created_at.desc()).all()
users = await User.sort(desc(User.created_at)).all()

# Sorting (mixed syntax)
users = await User.order_by('-created_at', User.name.asc()).all()
users = await User.sort('-age', desc(User.name)).all()

# Pagination
users = await User.offset(10).limit(5).all()  # Skip 10, take 5
users = await User.skip(10).take(5).all()     # Same as above
```

### Eager Loading

#### Join Loading

```python
# Left outer join
comment = await Comment.join(Comment.user, Comment.post).first()

comment = await Comment.join(
    Comment.user,
    (Comment.post, True)  # True means inner join
).first()

comments = await Comment.join(Comment.user, Comment.post).unique_all()
```

#### Subquery Loading

```python
# Using subquery loading
users = await User.with_subquery(
    User.posts,
    (User.comments, True)  # True means selectinload
).all()

# With limiting and sorting (important for correct results)
users = await User.with_subquery(User.posts)
    .limit(1)
    .sort('id')  # important!
    .all()
```

#### Complex Schema Loading

```python
from sqlactive import JOINED, SUBQUERY

schema = {
    User.posts: JOINED,  # joinedload user
    User.comments: (SUBQUERY, {  # load comments in separate query
        Comment.user: JOINED  # but join user in this separate query
    })
}

user = await User.with_schema(schema).first()
```

### Smart Queries

The `SmartQueryMixin` mixin provides a powerful smart query builder that combines
filtering, sorting, and eager loading:

```python
# Complex query with multiple features
users = await User.smart_query(
    criterion=(User.age > 18,),
    filters={'name__like': '%John%'},
    sort_columns=(User.username,),
    sort_attrs=['-created_at'],
    schema={User.posts: JOINED}
).all()
```

## Important Notes

1. When using `subqueryload()` with limiting modifiers (`limit()`, `offset()`),
   always include `order_by()` with unique columns (like primary key) to ensure
   correct results.

2. For joined eager loading with one-to-many or many-to-many relationships,
   use the `unique()` method or unique-related methods (i.e. `unique_all()`) to
   prevent duplicate rows:
   ```python
   users = await User.options(joinedload(User.posts)).unique_all()
   ```

## Error Handling

The mixin includes proper error handling for common scenarios:

- `NoResultFound`: Raised when a query expecting one result finds none.
- `MultipleResultsFound`: Raised when a query expecting one result finds multiple.
- `InvalidRequestError`: Raised for invalid query operations.
- `KeyError`: Raised when trying to set non-existent attributes.

All database operations are wrapped in try-except blocks with automatic rollback
on failure.

## API Reference

Check the [API Reference](/docs/ACTIVE_RECORD_API.md) for the full list of
available methods.

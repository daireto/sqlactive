# TimestampMixin Documentation

The `TimestampMixin` class provides automatic timestamp functionality for SQLAlchemy models.

## Customization

### Columns

You can customize the timestamp columns by setting the `__created_at_name__` and `__updated_at_name__` class attributes:

```python
class MyModel(TimestampMixin):
    __created_at_name__ = 'created_at'
    __updated_at_name__ = 'updated_at'
```

### Datetime function

You can customize the datetime function by setting the `__datetime_func__` class attribute:

```python
from sqlalchemy.sql import func

class MyModel(TimestampMixin):
    __datetime_func__ = func.current_timestamp()
```

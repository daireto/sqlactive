"""Models for testing."""

from typing import Optional
from sqlalchemy import ForeignKey, String
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlactive.base_model import ActiveRecordBaseModel


class BaseModel(ActiveRecordBaseModel):
    __abstract__ = True


class User(BaseModel):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    username: Mapped[str] = mapped_column(String(18), nullable=False, unique=True)
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

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    body: Mapped[str] = mapped_column(nullable=False)
    rating: Mapped[int] = mapped_column(nullable=False)
    topic: Mapped[Optional[str]] = mapped_column(String(50))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))

    user: Mapped['User'] = relationship(back_populates='posts')
    comments: Mapped[list['Comment']] = relationship(back_populates='post')


class Comment(BaseModel):
    __tablename__ = 'comments'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    body: Mapped[str] = mapped_column(nullable=False)
    post_id: Mapped[int] = mapped_column(ForeignKey('posts.id'))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))

    post: Mapped['Post'] = relationship(back_populates='comments')
    user: Mapped['User'] = relationship(back_populates='comments')


class Product(BaseModel):
    __tablename__ = 'products'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[float] = mapped_column(nullable=False)

    sells: Mapped[list['Sell']] = relationship(back_populates='product', viewonly=True)


class Sell(BaseModel):
    __tablename__ = 'sells'

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'), primary_key=True)
    quantity: Mapped[int] = mapped_column(nullable=False)

    product: Mapped['Product'] = relationship(back_populates='sells')

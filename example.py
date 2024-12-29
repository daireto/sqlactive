import asyncio

from sqlactive import DBConnection

from tests._models import BaseModel, User, Post, Comment


DATABASE_URL = 'sqlite+aiosqlite://'
conn = DBConnection(DATABASE_URL, echo=False)


async def main():
    bob = await User.create(username='Bob28', name='Bob Williams', age=30)
    print(bob)
    print(bob.created_at)

    await asyncio.sleep(1)

    # Update using `save` method
    bob.name = 'Bobby Williams'
    bob.age = 32
    await bob.save()

    # Update using `update` method
    await bob.update(name='Bobby Williams', age=32)
    print(bob.updated_at)

    # Serialize to dict
    print(bob.to_dict())

    user = await User.get(1)
    print(user)

    post = await Post.create(
        title='Lorem ipsum',
        rating=4,
        user=bob,
        body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
    )
    print(post)

    comment = await Comment.create(
        post=post,
        user=bob,
        body='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
    )
    print(comment)

    # filter using operators like 'in' and 'like' and relations like 'user'
    # will output this beauty: <Post #1 body:'Post1' user:'Bill'>
    result = await Post.where(rating__in=[2, 3, 4], user___name__like='%Bi%').all()
    print('all posts', result)

    # joinedload post and user
    result = await Comment.join(Comment.user, Comment.post).first()
    print('first comment', result)

    # subqueryload posts
    result = await User.with_subquery(User.posts).first()
    print('first user', result)
    if result:
        print('first user posts', result.posts)

        # serialize to dict, with relationships
        print(result.to_dict(nested=True))

    # sort by rating DESC, user name ASC
    result = await Post.sort('-rating', 'user___name').all()
    print('all posts sorted', result)

    # Using find and sort
    result = await Post.find(rating__in=[2, 3, 4]).sort('-rating', 'user___name').take(2).all()
    print('all posts sorted using find', result)

    result = await Post.join(Post.user).filter(user___name='Bob').first()
    print(result)
    await bob.delete()
    result = await Post.join(Post.user).filter(user___name='Bob').first()
    print(result)


if __name__ == '__main__':
    asyncio.run(conn.init_db(BaseModel))
    asyncio.run(main())

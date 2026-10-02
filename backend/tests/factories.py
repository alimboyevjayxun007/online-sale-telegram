from app.models import User


async def make_user(session, uid: int = 5001, **kw) -> User:
    user = User(id=uid, username=kw.pop("username", f"user{uid}"), first_name=kw.pop("first_name", "Test"), **kw)
    session.add(user)
    await session.flush()
    return user

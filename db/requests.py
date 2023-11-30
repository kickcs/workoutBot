from db.models import User
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import async_sessionmaker
from db.models import sessionmaker


async def create_user(tg_id: int):
    async with sessionmaker() as session:
        session.add(User(tg_id=tg_id))
        await session.commit()

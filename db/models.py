from sqlalchemy import BigInteger, ForeignKey, String, Date
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from config import config

engine = create_async_engine(url=config.db_url, echo=False)
sessionmaker = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase, AsyncAttrs):
    pass


class Users(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True)


class Exercises(Base):
    __tablename__ = 'exercises'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey(Users.tg_id))
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(255))


class Trains(Base):
    __tablename__ = 'trains'

    id: Mapped[int] = mapped_column(primary_key=True)
    exercise_id: Mapped[int] = mapped_column(ForeignKey(Exercises.id))
    type: Mapped[str] = mapped_column(String(255))
    set_number: Mapped[int]
    reps: Mapped[int]
    weight: Mapped[int]
    date: Mapped[str] = mapped_column(Date)


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

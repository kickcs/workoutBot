from db.models import Users, Exercises, Trains
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import async_sessionmaker
from db.models import sessionmaker


async def create_user(tg_id: int):
    async with sessionmaker() as session:
        session.add(Users(tg_id=tg_id))
        await session.commit()


async def get_user(tg_id: int) -> Users | None:
    async with sessionmaker() as session:
        result = await session.execute(select(Users).where(Users.tg_id == tg_id))
        user = result.scalar_one_or_none()
        return user


async def add_exercise(tg_id: int, name: str, exercise_type: str):
    async with sessionmaker() as session:
        session.add(Exercises(user_id=tg_id, name=name, type=exercise_type))
        await session.commit()


async def delete_exercise(tg_id: int, exercise_id: int):
    async with sessionmaker() as session:
        exercise_id = int(exercise_id)
        await session.execute(delete(Exercises).where(Exercises.id == exercise_id, Exercises.user_id == tg_id))
        await session.commit()


async def list_exercises(tg_id: int):
    async with sessionmaker() as session:
        result = await session.execute(select(Exercises).where(Exercises.user_id == tg_id))
        exercises = result.scalars().all()
        return exercises


async def get_exercise_types(tg_id: int):
    async with sessionmaker() as session:
        result = await session.execute(select(Exercises.type).distinct().where(Exercises.user_id == tg_id))
        exercise_types = result.scalars().all()
        return exercise_types


async def get_exercises_by_type(tg_id: int, exercise_type: str):
    async with sessionmaker() as session:
        result = await session.execute(
            select(Exercises)
            .where(Exercises.user_id == tg_id, Exercises.type == exercise_type)
        )
        exercises = result.scalars().all()
        return exercises


async def get_exercise_name(tg_id: int, exercise_id: int):
    async with sessionmaker() as session:
        result = await session.execute(
            select(Exercises.name)
            .where(Exercises.user_id == tg_id, Exercises.id == int(exercise_id))
        )
        exercise_name = result.scalar_one_or_none()
        return exercise_name


async def create_train(exercise_id: int, ex_type: str, set_number: int, reps: int, weight: int, date: str):
    async with sessionmaker() as session:
        session.add(Trains(exercise_id=exercise_id, type=ex_type, set_number=set_number, reps=reps, weight=weight,
                           date=date))
        await session.commit()

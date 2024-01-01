from db.models import Users, Exercises, Trains
from sqlalchemy import select, delete, join, func
from db.models import sessionmaker
from datetime import datetime


# Класс для работы с пользователями
class UserRepository:
    @staticmethod
    async def create_user(tg_id: int):
        async with sessionmaker() as session:
            session.add(Users(tg_id=tg_id))
            await session.commit()

    @staticmethod
    async def get_user(tg_id: int) -> Users | None:
        async with sessionmaker() as session:
            result = await session.execute(select(Users).where(Users.tg_id == tg_id))
            return result.scalar_one_or_none()


# Класс для работы с упражнениями
class ExerciseRepository:
    @staticmethod
    async def add_exercise(tg_id: int, name: str, exercise_type: str):
        async with sessionmaker() as session:
            session.add(Exercises(user_id=tg_id, name=name, type=exercise_type))
            await session.commit()

    @staticmethod
    async def delete_exercise(tg_id: int, exercise_id: int):
        async with sessionmaker() as session:
            await session.execute(delete(Trains).where(Trains.exercise_id == int(exercise_id)))
            await session.execute(delete(Exercises).where(Exercises.id == int(exercise_id)), Exercises.user_id == tg_id)
            await session.commit()

    @staticmethod
    async def list_exercises(tg_id: int):
        async with sessionmaker() as session:
            result = await session.execute(select(Exercises).where(Exercises.user_id == tg_id))
            return result.scalars().all()

    @staticmethod
    async def get_exercise_types(tg_id: int):
        async with sessionmaker() as session:
            result = await session.execute(select(Exercises.type).distinct().where(Exercises.user_id == tg_id))
            exercise_types = result.scalars().all()
            return exercise_types

    @staticmethod
    async def get_exercises_by_type(tg_id: int, exercise_type: str):
        async with sessionmaker() as session:
            result = await session.execute(
                select(Exercises)
                .where(Exercises.user_id == tg_id, Exercises.type == exercise_type)
            )
            exercises = result.scalars().all()
            return exercises

    @staticmethod
    async def get_exercise_name(tg_id: int, exercise_id: int):
        async with sessionmaker() as session:
            result = await session.execute(
                select(Exercises.name)
                .where(Exercises.user_id == tg_id, Exercises.id == int(exercise_id))
            )
            exercise_name = result.scalar_one_or_none()
            return exercise_name

    @staticmethod
    async def get_available_exercises(tg_id: int):
        async with sessionmaker() as session:
            result = await session.execute(
                select(Exercises.id, Exercises.name, Exercises.type)
                .where(Exercises.user_id == tg_id)
            )
            exercises = result.first()
            return exercises is not None

    @staticmethod
    async def add_default_exercises(tg_id: int, workout_plan: dict):
        async with sessionmaker() as session:
            for muscle_group, exercises in workout_plan.items():
                for exercise_name in exercises:
                    session.add(Exercises(user_id=tg_id, name=exercise_name, type=muscle_group))
            await session.commit()


# Класс для работы с тренировками
class TrainRepository:
    @staticmethod
    async def create_train(exercise_id: int, ex_type: str, set_number: int, reps: int, weight: int, date: str):
        async with sessionmaker() as session:
            session.add(Trains(exercise_id=exercise_id, type=ex_type, set_number=set_number, reps=reps, weight=weight,
                               date=date))
            await session.commit()

    @staticmethod
    async def get_trains_by_id(train_id: int):
        async with sessionmaker() as session:
            result = await session.execute(
                select(Trains)
                .where(Trains.exercise_id == int(train_id))
            )
            trains = result.scalars().all()
            return trains


class ProfileRepository:
    @staticmethod
    async def get_date_trains_profile(tg_id: int):
        async with sessionmaker() as session:
            result = await session.execute(
                select(Trains.date)
                .join(Exercises, Exercises.id == Trains.exercise_id)
                .where(Exercises.user_id == tg_id)
                .distinct(Trains.date)
                .order_by(Trains.date.desc())
            )
            train_data = result.all()
        return train_data

    @staticmethod
    async def get_train_profile(tg_id: int, date: str):
        async with sessionmaker() as session:
            specific_date_obj = datetime.strptime(date, "%Y-%m-%d").date()

            result = await session.execute(
                select(
                    Trains.date,
                    Trains.set_number,
                    Trains.reps,
                    Trains.weight,
                    Exercises.name
                )
                .join(Exercises, Trains.exercise_id == Exercises.id)
                .where(
                    (Exercises.user_id == tg_id) &
                    (Trains.date == specific_date_obj)
                )
            )
            trains = result.all()
            return trains

from aiogram.fsm.state import State, StatesGroup


class Main(StatesGroup):
    MAIN = State()


class Exercises(StatesGroup):
    MAIN = State()
    ADD_NAME = State()
    ADD_TYPE = State()
    EDIT = State()
    LIST = State()


class Trains(StatesGroup):
    MAIN = State()
    ADD = State()
    EDIT = State()
    LIST = State()

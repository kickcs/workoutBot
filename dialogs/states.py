from aiogram.fsm.state import State, StatesGroup


class Main(StatesGroup):
    MAIN = State()

class Info(StatesGroup):
    MAIN = State()

class Exercises(StatesGroup):
    MAIN = State()
    ADD_NAME = State()
    ADD_TYPE = State()
    EDIT = State()
    LIST = State()
    DEFAULT_EXERCISE = State()


class Trains(StatesGroup):
    MAIN = State()
    LIST = State()
    SETS = State()
    RECORD_SET = State()
    RECORD_WEIGHT = State()


class Profile(StatesGroup):
    MAIN = State()
    TRAINS = State()
    TRAINS_INFO = State()
    EXERCISES = State()
    EXERCISES_INFO = State()

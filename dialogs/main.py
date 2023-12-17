from aiogram_dialog import Dialog, Window, LaunchMode, DialogManager
from aiogram_dialog.widgets.kbd import Start
from aiogram_dialog.widgets.text import Const
from aiogram import F

from db.requests import ExerciseRepository

from . import states


async def getter(dialog_manager: DialogManager, **_kwargs):
    tg_id = dialog_manager.middleware_data['event_from_user'].id
    exercises = await ExerciseRepository.get_available_exercises(tg_id=tg_id)
    if exercises:
        return {'trains': True}
    return {'trains': False}


main_dialog = Dialog(
    Window(
        Const(
            "<b>🏋️ Добро пожаловать в Fitness Tracker Bot! 🏋️</b>\n\n"
            "Этот бот поможет вам следить за вашими достижениями в спортзале, "
            "записывая и анализируя ваш прогресс в упражнениях. Основные возможности:\n\n"
            "<b>1. Отслеживание прогресса</b> - Записывайте количество повторений и вес, "
            "используемый в каждом подходе, и следите за тем, как улучшаются ваши результаты со временем.\n\n"
            "<b>2. История тренировок</b> - Просматривайте историю всех ваших упражнений, "
            "чтобы видеть, как вы растете в силе и выносливости.\n\n"
            "<b>3. Персонализированные упражнения</b> - Создавайте и управляйте своими упражнениями, "
            "настраивая тренировочные планы под свои цели.\n\n"
            "<b>4. Анализ данных</b> - Получайте аналитику о вашем прогрессе, чтобы лучше понимать, "
            "какие упражнения наиболее эффективны для вас.\n\n"
            "Начните свой путь к совершенству тела уже сегодня! Выберите опцию в меню чтобы начать."
        ),
        Start(
            text=Const('Информация'),
            id='info',
            state=states.Info.MAIN
        ),
        Start(
            text=Const('Упражнения'),
            id='exercises',
            state=states.Exercises.MAIN
        ),
        Start(
            text=Const('Профиль'),
            id='profile',
            state=states.Profile.MAIN,
            when=F['trains']
        ),
        Start(
            text=Const('Начать тренировку'),
            id='trains',
            state=states.Trains.MAIN,
            when=F['trains']),
        state=states.Main.MAIN,
        getter=getter
    ),
    launch_mode=LaunchMode.ROOT
)

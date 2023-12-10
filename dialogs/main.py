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
        Const('Test'),
        Const('Для получения подробной информации \n'
              'о работе с ботом нажмите "Информация"'),
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

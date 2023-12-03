from aiogram_dialog import Dialog, Window, LaunchMode
from aiogram_dialog.widgets.kbd import Start, Button
from aiogram_dialog.widgets.text import Const

from . import states

main_dialog = Dialog(
    Window(
        Const('Test'),
        Const('Для получения подробной информации \n'
              'о работе с ботом нажмите "Информация"'),
        Button(text=Const('Информация ### IN PROGRESS'), id='info'),
        Start(
            text=Const('Упражнения'),
            id='exercises',
            state=states.Exercises.MAIN
        ),
        Start(
            text=Const('Начать тренировку ### IN PROGRESS'),
            id='trains',
            state=states.Trains.MAIN
        ),
        state=states.Main.MAIN
    ),
    launch_mode=LaunchMode.ROOT
)

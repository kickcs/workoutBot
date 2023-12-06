from aiogram_dialog import Dialog, Window, LaunchMode
from aiogram_dialog.widgets.kbd import Start, Button
from aiogram_dialog.widgets.text import Const

from . import states

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
            text=Const('Начать тренировку'),
            id='trains',
            state=states.Trains.MAIN
        ),
        state=states.Main.MAIN
    ),
    launch_mode=LaunchMode.ROOT
)

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Start
from aiogram_dialog.widgets.text import Const

from . import states


info_dialog = Dialog(
    Window(
        Const('Test'),
        Start(Const('Назад'), id='__main__', state=states.Main.MAIN),
        state=states.Info.MAIN
    )
)
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Start
from aiogram_dialog.widgets.text import Const

from . import states


main_profile_window = Window(
        Const('Test'),
        Start(Const('Назад'), id='__main__', state=states.Main.MAIN),
        state=states.Profile.MAIN
    )

profile_dialog = Dialog(
    main_profile_window
)
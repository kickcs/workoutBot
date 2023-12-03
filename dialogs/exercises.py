from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import (ScrollingGroup, Back, SwitchTo,
                                        Select, Group, Start)
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog import ChatEvent

from aiogram.types import ContentType, Message, CallbackQuery
from typing import Any

from . import states
from db.requests import add_exercise, list_exercises, delete_exercise


async def name_handler(message: Message, message_input: MessageInput,
                       manager: DialogManager):
    if manager.is_preview():
        await manager.next()
        return
    manager.dialog_data['exercise_name'] = message.text
    await manager.next()


async def other_type_handler(message: Message, message_input: MessageInput,
                             manager: DialogManager):
    await message.answer('Мне кажется ваше сообщение не похоже на текст =)')


async def exercise_type_handler(callback: ChatEvent, select: Any,
                                manager: DialogManager, item_id: str):
    manager.dialog_data['exercise_type'] = item_id
    await add_exercise(tg_id=manager.event.from_user.id,
                       name=manager.dialog_data['exercise_name'],
                       exercise_type=manager.dialog_data['exercise_type'])
    await manager.switch_to(state=states.Exercises.MAIN)


async def getter(dialog_manager: DialogManager, **_kwargs):
    exercises = await list_exercises(tg_id=dialog_manager.event.from_user.id)
    return {'exercises': exercises}


async def on_exercise_selected(callback: CallbackQuery, widget: Any,
                               manager: DialogManager, selected_item: str):
    await callback.answer(selected_item)


async def on_edited_exercise_selected(callback: CallbackQuery, widget: Any,
                                      manager: DialogManager, selected_item: int):
    await delete_exercise(tg_id=manager.event.from_user.id, exercise_id=selected_item)


HEADER = Const('###')
# region main window + add window
main_window = Window(
    HEADER,
    SwitchTo(Const('Добавить упражнение'), id='add_exercise', state=states.Exercises.ADD_NAME),
    SwitchTo(Const('Редактировать упражнение'), id='edit_exercise', state=states.Exercises.EDIT),
    SwitchTo(Const('Список упражнений'), id='list_exercises', state=states.Exercises.LIST),
    Start(text=Const('Назад'), id="__main__", state=states.Main.MAIN),
    state=states.Exercises.MAIN
)
add_name_window = Window(
    Const('Введите название упражнения'),
    MessageInput(name_handler, content_types=[ContentType.TEXT]),
    MessageInput(other_type_handler),
    SwitchTo(text=Const('Назад'), id='back', state=states.Exercises.MAIN),
    state=states.Exercises.ADD_NAME
)
add_type_window = Window(
    Const('Выберите группу мышц, соответствующую упражнению'),
    Group(Select(
        Format("{item}"),
        items=['Грудь', 'Спина', 'Плечи', 'Ноги', 'Бицепс', 'Трицепс', 'Прочее'],
        item_id_getter=lambda item: item,
        id='exercise_type',
        on_click=exercise_type_handler
    ), width=2),
    Back(text=Const('Назад'), id='back'),
    state=states.Exercises.ADD_TYPE,
)
# endregion

list_exercises_window = Window(
    Const('Список упражнений'),
    ScrollingGroup(Select(
        Format("{item.name} | ({item.type})"),
        id="s_exercises",
        item_id_getter=lambda item: item.id,
        items='exercises',
        on_click=on_exercise_selected
    ), width=1, height=8, id='list_exercises'),
    Back(text=Const('Назад'), id='back'),
    state=states.Exercises.LIST,
    getter=getter,
)

edit_exercise_window = Window(
    Const('Выберите упражнение, которое хотите удалить из списка'),
    ScrollingGroup(Select(
        Format("{item.name} | ({item.type})"),
        id="s_exercises",
        item_id_getter=lambda item: item.id,
        items='exercises',
        on_click=on_edited_exercise_selected
    ), width=1, height=8, id='list_exercises'),
    SwitchTo(text=Const('Назад'), id='back', state=states.Exercises.MAIN),
    state=states.Exercises.EDIT,
    getter=getter,
)

exercises_dialog = Dialog(
    main_window,
    list_exercises_window,
    add_name_window,
    add_type_window,
    edit_exercise_window
)

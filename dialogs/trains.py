from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import (Back, SwitchTo, Select, Group, Start, Column, Button)
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog import ChatEvent

from aiogram.types import Message, CallbackQuery
from typing import Any
import operator

from . import states
from db.requests import get_exercise_types, get_exercises_by_type, get_exercise_name


async def generate_approaches(number: int):
    approaches = []
    for i in range(1, number+1):
        approaches.append((f'Подход {i}', i))
    return approaches


async def exercise_types_getter(dialog_manager: DialogManager, **_kwargs):
    exercise_types = await get_exercise_types(tg_id=dialog_manager.event.from_user.id)
    return {'exercise_type': exercise_types}


async def on_exercise_type_selected(callback: CallbackQuery, widget: Any,
                                    manager: DialogManager, selected_item: str):
    manager.dialog_data['exercise_type'] = selected_item
    await manager.next()


async def exercise_by_type_getter(dialog_manager: DialogManager, **_kwargs):
    exercises = await get_exercises_by_type(tg_id=dialog_manager.event.from_user.id,
                                            exercise_type=dialog_manager.dialog_data['exercise_type'])
    return {'exercises': exercises}


async def on_exercise_selected(callback: CallbackQuery, widget: Any,
                               manager: DialogManager, selected_item: str):
    manager.dialog_data['exercise_id'] = selected_item
    await manager.next()


async def exercise_set_getter(dialog_manager: DialogManager, **_kwargs):
    exercise_name = await get_exercise_name(tg_id=dialog_manager.event.from_user.id,
                                            exercise_id=dialog_manager.dialog_data['exercise_id'])
    sets = dialog_manager.dialog_data.get('sets', 0)
    if sets:
        sets_data = await generate_approaches(sets)
        return {'exercise_name': exercise_name, 'sets': sets_data, 'show': True}
    else:
        return {'exercise_name': exercise_name, 'show': False}


async def on_button_selected(callback: CallbackQuery, widget: Button,
                             manager: DialogManager):
    manager.current_context().dialog_data.setdefault('sets', 0)

    if widget.widget_id == 'add_set':
        manager.current_context().dialog_data['sets'] += 1
    elif widget.widget_id == 'delete_set':
        manager.current_context().dialog_data['sets'] -= 1


# region first_windows
window_type_select = Window(
    Const('Выберите нужную группу упражнений'),
    Column(Select(
        Format("{item}"),
        id='exercise_type',
        item_id_getter=lambda item: item,
        items='exercise_type',
        on_click=on_exercise_type_selected,
    )),
    Start(text=Const('Назад'), id="__main__", state=states.Main.MAIN),
    state=states.Trains.MAIN,
    getter=exercise_types_getter
)

window_exercise_select = Window(
    Const('Выберите нужное вам упражнение'),
    Column(Select(
        Format("{item.name}"),
        id='s_exercises',
        item_id_getter=lambda item: item.id,
        items='exercises',
        on_click=on_exercise_selected
    )),
    Back(text=Const('Назад')),
    getter=exercise_by_type_getter,
    state=states.Trains.LIST
)
# endregion

window_exercise_set_select = Window(
    Format('Текущее упражнение:\n{exercise_name}'),
    Column(Select(
        Format("{item[0]}"),
        id='s_sets',
        item_id_getter=operator.itemgetter(1),
        items='sets',
        when='show'
    )),
    Button(Const('Добавить подход'), id='add_set', on_click=on_button_selected),
    Button(Const('Удалить подход'), id='delete_set', on_click=on_button_selected),
    Back(text=Const('Назад')),
    state=states.Trains.SETS,
    getter=exercise_set_getter
)

trains_dialog = Dialog(
    window_type_select,
    window_exercise_select,
    window_exercise_set_select
)

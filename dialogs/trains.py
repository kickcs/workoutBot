from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import (Back, Select, Start, Column, Button)
from aiogram_dialog.widgets.text import Const, Format, Case
from aiogram_dialog.widgets.input import MessageInput

from aiogram.types import Message, CallbackQuery, ContentType
from aiogram import F
from typing import Any
from datetime import datetime
import operator

from . import states
from db.requests import (get_exercise_types, get_exercises_by_type, get_exercise_name,
                         create_train)


async def generate_approaches(number: int, exercises: dict | None, exercise_id: str):
    """Generates list of approaches"""
    approaches = []

    if exercises is None:
        for i in range(1, number + 1):
            approaches.append((f'Подход {i}', i, None, None, False))
    else:
        exercise_sets = exercises.get(exercise_id, [])

        for i in range(1, number + 1):
            found_set = next((set_info for set_info in exercise_sets if int(set_info['set_number']) == i), None)

            if found_set:
                approaches.append((f'Подход {i}', i, found_set['reps'], found_set['weight'], True))
            else:
                approaches.append((f'Подход {i}', i, None, None, False))

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
    return {'exercises': exercises, }


async def on_exercise_selected(callback: CallbackQuery, widget: Any,
                               manager: DialogManager, selected_item: str):
    manager.dialog_data['exercise_id'] = selected_item
    await manager.next()


async def exercise_set_getter(dialog_manager: DialogManager, **_kwargs):
    exercise_id = dialog_manager.dialog_data['exercise_id']
    exercise_name = await get_exercise_name(tg_id=dialog_manager.event.from_user.id,
                                            exercise_id=exercise_id)
    exercise_sets = dialog_manager.current_context().dialog_data.get('exercise_sets', {})

    sets_count = exercise_sets.get(dialog_manager.dialog_data['exercise_id'], 0)
    sets = await generate_approaches(sets_count, dialog_manager.dialog_data.get('exercises'),
                                     exercise_id)
    print(dialog_manager.dialog_data)
    return {'exercise_name': exercise_name, 'sets': sets}


async def on_button_selected(callback: CallbackQuery, widget: Button,
                             manager: DialogManager):
    exercise_id = str(manager.current_context().dialog_data['exercise_id'])
    exercise_sets = manager.current_context().dialog_data.setdefault('exercise_sets', {})

    if exercise_id not in exercise_sets:
        exercise_sets[exercise_id] = 0

    if widget.widget_id == 'add_set':
        exercise_sets[exercise_id] += 1
    elif widget.widget_id == 'delete_set' and exercise_sets[exercise_id] > 0:
        exercise_sets[exercise_id] -= 1


async def on_exercise_sets_selected(callback: CallbackQuery, widget: Any,
                                    manager: DialogManager, selected_item: int):
    manager.dialog_data['set_number'] = selected_item
    exercise_id = manager.current_context().dialog_data['exercise_id']
    if 'exercises' not in manager.dialog_data:
        manager.dialog_data['exercises'] = {}
    if exercise_id not in manager.dialog_data['exercises']:
        manager.dialog_data['exercises'][exercise_id] = []

        # Создаем словарь для нового подхода с данными из callback
    if not any(set_info['set_number'] == selected_item for set_info in manager.dialog_data['exercises'][exercise_id]):
        new_set = {
            'set_number': selected_item,
            'reps': None,
            'weight': None
        }

        # Добавляем информацию о новом подходе в список для соответствующего exercise_id
        manager.dialog_data['exercises'][exercise_id].append(new_set)

    # Выводим обновленную структуру данных для проверки
    print(manager.current_context().dialog_data)
    await manager.next()


async def exercise_name_getter(dialog_manager: DialogManager, **_kwargs):
    exercise_name = await get_exercise_name(tg_id=dialog_manager.event.from_user.id,
                                            exercise_id=dialog_manager.dialog_data['exercise_id'])
    return {'exercise_name': exercise_name}


async def count_reps_set(message: Message, message_input: MessageInput,
                         manager: DialogManager):
    exercise_id = manager.current_context().dialog_data['exercise_id']

    if manager.is_preview():
        await manager.next()
        return

    current_set_number = manager.current_context().dialog_data['set_number']

    for set_detail in manager.dialog_data['exercises'][exercise_id]:
        if set_detail['set_number'] == current_set_number:
            set_detail['reps'] = message.text
            break

    await manager.next()


async def count_weight_set(message: Message, message_input: MessageInput,
                           manager: DialogManager):
    exercise_id = manager.current_context().dialog_data['exercise_id']

    if manager.is_preview():
        await manager.next()
        return

    current_set_number = manager.current_context().dialog_data['set_number']

    for set_detail in manager.dialog_data['exercises'][exercise_id]:
        if set_detail['set_number'] == current_set_number:
            set_detail['weight'] = message.text
            break

    await manager.switch_to(state=states.Trains.SETS)


async def other_type_handler(message: Message, message_input: MessageInput,
                             manager: DialogManager):
    await message.answer('Вы ввели некорректное значение. Пожалуйста, попробуйте ещё раз\n'
                         'Ваш ответ должен состоять только из целых чисел!')


async def end_trains(callback: CallbackQuery, widget: Button,
                     manager: DialogManager):
    data = manager.dialog_data['exercises']
    for exercise_id, sets in data.items():
        for set_info in sets:
            await create_train(
                exercise_id=exercise_id,
                ex_type='normal',
                set_number=set_info['set_number'],
                reps=set_info['reps'],
                weight=set_info['weight'],
                date=datetime.now().strftime('%Y-%m-%d')
            )

    await callback.answer(text='Вы успешно завершили тренировку')
    await manager.done()
    await manager.switch_to(state=states.Main.MAIN)


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
    Button(text=Const('Закончить тренировку'), id='finish', on_click=end_trains),
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
        Format("{item[0]} | {item[2]}x{item[3]} кг"),
        id='s_sets',
        item_id_getter=operator.itemgetter(1),
        items='sets',
        on_click=on_exercise_sets_selected
    )),
    Button(Const('Добавить подход'), id='add_set', on_click=on_button_selected),
    Button(Const('Удалить подход'), id='delete_set', on_click=on_button_selected),
    Back(text=Const('Назад')),
    state=states.Trains.SETS,
    getter=exercise_set_getter
)

window_exercise_set_reps_input = Window(
    Format('Текущее упражнение:\n{exercise_name}\n'),
    Const('Введите количество сделанных повторений:'),
    MessageInput(count_reps_set, content_types=[ContentType.TEXT], filter=F.text.isdigit()),
    MessageInput(other_type_handler),
    Back(text=Const('Назад')),
    getter=exercise_name_getter,
    state=states.Trains.RECORD_SET
)

window_exercise_set_weight_input = Window(
    Format('Текущее упражнение:\n{exercise_name}\n'),
    Const('Введите вес, который вы использовали в данном подходе:'),
    MessageInput(count_weight_set, content_types=[ContentType.TEXT], filter=F.text.isdigit()),
    MessageInput(other_type_handler),
    Back(text=Const('Назад')),
    getter=exercise_name_getter,
    state=states.Trains.RECORD_WEIGHT
)

trains_dialog = Dialog(
    window_type_select,
    window_exercise_select,
    window_exercise_set_select,
    window_exercise_set_reps_input,
    window_exercise_set_weight_input
)

from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import (Back, Select, Start, Column, Button)
from aiogram_dialog.widgets.text import Const, Format, Jinja
from aiogram_dialog.widgets.input import MessageInput

from aiogram.types import Message, CallbackQuery, ContentType
from aiogram import F
import asyncio
from typing import Any
from datetime import datetime
import operator

from . import states
from db.requests import ExerciseRepository, TrainRepository


async def generate_approaches(number: int, exercises: dict | None, exercise_id: str):
    """Generates list of approaches"""
    approaches = []

    if exercises is None:
        for i in range(1, number + 1):
            approaches.append((f'Подход {i}', i, None, None))
    else:
        exercise_sets = exercises.get(exercise_id, [])

        for i in range(1, number + 1):
            found_set = next((set_info for set_info in exercise_sets if int(set_info['set_number']) == i), None)

            if found_set:
                approaches.append((f'Подход {i}', i, found_set['reps'], found_set['weight']))
            else:
                approaches.append((f'Подход {i}', i, None, None))

    return approaches


async def exercise_types_getter(dialog_manager: DialogManager, **_kwargs):
    exercise_types = await ExerciseRepository.get_exercise_types(tg_id=dialog_manager.event.from_user.id)
    if dialog_manager.dialog_data.get('exercises'):
        return {'exercise_type': exercise_types, 'end_train': True}
    return {'exercise_type': exercise_types}


async def on_exercise_type_selected(callback: CallbackQuery, widget: Any,
                                    manager: DialogManager, selected_item: str):
    manager.dialog_data['exercise_type'] = selected_item
    await manager.next()


async def exercise_by_type_getter(dialog_manager: DialogManager, **_kwargs):
    exercises = await ExerciseRepository.get_exercises_by_type(tg_id=dialog_manager.event.from_user.id,
                                                               exercise_type=dialog_manager.dialog_data[
                                                                   'exercise_type'])
    return {'exercises': exercises, }


async def on_exercise_selected(callback: CallbackQuery, widget: Any,
                               manager: DialogManager, selected_item: str):
    manager.dialog_data['exercise_id'] = selected_item
    await manager.next()


async def exercise_set_getter(dialog_manager: DialogManager, **_kwargs):
    exercise_id = dialog_manager.dialog_data['exercise_id']
    exercise_name = await ExerciseRepository.get_exercise_name(tg_id=dialog_manager.event.from_user.id,
                                                               exercise_id=exercise_id)
    exercise_sets = dialog_manager.current_context().dialog_data.get('exercise_sets', {})

    sets_count = exercise_sets.get(dialog_manager.dialog_data['exercise_id'], 0)
    sets = await generate_approaches(sets_count, dialog_manager.dialog_data.get('exercises'),
                                     exercise_id)

    previous_sets = await TrainRepository.get_trains_by_id(train_id=exercise_id)

    # Оставляем только записи для трех последних дат

    unique_dates = set()
    unique_dates = set(train.date for train in previous_sets)

    return {'exercise_name': exercise_name, 'sets': sets, 'previous_sets': previous_sets,
            'unique_dates': unique_dates}


async def on_button_selected(callback: CallbackQuery, widget: Button, manager: DialogManager):
    exercise_id = str(manager.current_context().dialog_data['exercise_id'])
    exercise_sets = manager.current_context().dialog_data.setdefault('exercise_sets', {})

    # Инициализация словаря 'exercises', если он не существует
    if 'exercises' not in manager.dialog_data:
        manager.dialog_data['exercises'] = {}

    # Получаем список подходов для текущего упражнения
    current_exercise = manager.dialog_data['exercises'].get(exercise_id, [])

    # Изменяем количество подходов в зависимости от выбранной кнопки
    if widget.widget_id == 'add_set':
        exercise_sets[exercise_id] = exercise_sets.get(exercise_id, 0) + 1
    elif widget.widget_id == 'delete_set':
        # Проверяем, есть ли информация о последнем подходе
        if len(current_exercise) < exercise_sets.get(exercise_id, 0):
            # Уменьшаем количество подходов, так как последний подход не имеет деталей
            exercise_sets[exercise_id] = max(0, exercise_sets.get(exercise_id, 0) - 1)
        elif current_exercise:
            # Удаляем детали последнего подхода
            current_exercise.pop(-1)

        # Если больше нет подходов, удаляем упражнение из списка
        if not current_exercise and exercise_sets.get(exercise_id, 0) == 0:
            manager.dialog_data['exercises'].pop(exercise_id, None)

    # Обновляем списки подходов и упражнений в dialog_data
    if current_exercise:
        manager.dialog_data['exercises'][exercise_id] = current_exercise
    elif exercise_id in manager.dialog_data['exercises']:
        manager.dialog_data['exercises'].pop(exercise_id)

    manager.current_context().dialog_data['exercise_sets'] = exercise_sets


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

    await manager.next()


async def exercise_name_getter(dialog_manager: DialogManager, **_kwargs):
    exercise_name = await ExerciseRepository.get_exercise_name(tg_id=dialog_manager.event.from_user.id,
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
    await message.answer('⚠️ Вы ввели некорректное значение. Пожалуйста, попробуйте ещё раз.\n'
                         '🔢 Ваш ответ должен состоять только из целых чисел!')


async def end_trains(callback: CallbackQuery, widget: Button, manager: DialogManager):
    data = manager.dialog_data['exercises']
    tasks = []

    for exercise_id, sets in data.items():
        for set_info in sets:
            # Проверяем, что значения reps и weight не равны None
            if set_info['reps'] is not None and set_info['weight'] is not None:
                # Создаем асинхронную задачу для каждого вызова create_train
                task = TrainRepository.create_train(
                    exercise_id=exercise_id,
                    ex_type='normal',
                    set_number=set_info['set_number'],
                    reps=set_info['reps'],
                    weight=set_info['weight'],
                    date=datetime.now().strftime('%Y-%m-%d')
                )
                tasks.append(task)

    # Выполняем все задачи асинхронно
    if tasks:
        await asyncio.gather(*tasks)

    await callback.answer(text='Вы успешно завершили тренировку')
    await manager.done()
    await manager.switch_to(state=states.Main.MAIN)


# region first_windows
window_type_select = Window(
    Const('👋 <b>Выбор группы мышц</b>\n\n'
          'Для начала выберите группу мышц, для которой вы хотите подобрать упражнения:\n\n'
          'После выбора группы мышц, я покажу вам список подходящих упражнений. '),
    Column(Select(
        Format("{item}"),
        id='exercise_type',
        item_id_getter=lambda item: item,
        items='exercise_type',
        on_click=on_exercise_type_selected,
    )),
    Button(text=Const('Закончить тренировку'),
           id='finish',
           on_click=end_trains,
           when=F['end_train']),
    Start(text=Const('Назад'), id="__main__", state=states.Main.MAIN),
    state=states.Trains.MAIN,
    getter=exercise_types_getter
)

window_exercise_select = Window(
    Const('🏋️ <b>Выбор Упражнения </b>\n\n'
          'Выберите упражнение из списка ниже.'),
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
    Jinja('''
<b>🏋️ Текущее упражнение:</b> {{ exercise_name }}\n
{% if previous_sets %}
<b>📅 Прошлые тренировки:</b>
{% for date in unique_dates %}
\n<b>🗓️ Дата:</b> {{ date.strftime('%A, %d-%m-%Y') }}
{% for train_set in previous_sets %}
{% if train_set.date == date %}
   - {{ train_set.set_number }}: {{ train_set.reps }}х{{ train_set.weight }} кг
{% endif %}
{% endfor %}
{% endfor %}
{% else %}
<i>🚫 Информация о прошлых тренировках отсутствует.</i>
{% endif %}
'''),
    Column(Select(
        Jinja(
            "{% if item[2] is not none and item[3] is not none %}"
            "{{ item[0] }} | {{ item[2] }}x{{ item[3] }} кг"
            "{% else %}"
            "{{ item[0] }}"
            "{% endif %}"
        ),
        id='s_sets',
        item_id_getter=operator.itemgetter(1),
        items='sets',
        on_click=on_exercise_sets_selected,
    )),
    Button(Const('Добавить подход'), id='add_set', on_click=on_button_selected),
    Button(text=Const('Удалить подход'),
           id='delete_set',
           on_click=on_button_selected,
           when=F['dialog_data']['exercise_sets']),
    Back(text=Const('Назад')),
    parse_mode='HTML',
    state=states.Trains.SETS,
    getter=exercise_set_getter
)

window_exercise_set_reps_input = Window(
    Format('🏋️ Текущее упражнение:\n{exercise_name}\n'),
    Const('🔢 Введите количество сделанных повторений:'),
    MessageInput(count_reps_set, content_types=[ContentType.TEXT], filter=F.text.isdigit()),
    MessageInput(other_type_handler),
    Back(text=Const('Назад')),
    getter=exercise_name_getter,
    state=states.Trains.RECORD_SET
)

window_exercise_set_weight_input = Window(
    Format('🏋️ Текущее упражнение:\n{exercise_name}\n'
           '⚖️ Введите вес, который вы использовали в данном подходе:'),
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

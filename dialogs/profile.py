from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Start, Back, Select, SwitchTo, ScrollingGroup
from aiogram_dialog.widgets.text import Const, Jinja
from aiogram.types import CallbackQuery

from db.requests import ProfileRepository
import operator
from . import states
from typing import Any
from collections import defaultdict


async def group_trains_by_exercise(trains):
    grouped = {}
    for train in trains:
        # Использование индекса 4 для доступа к имени упражнения (Exercises.name)
        key = train[4]
        if key not in grouped:
            grouped[key] = []
        # Добавление всего кортежа или создание нового объекта, если необходимо
        grouped[key].append(train)
    # Опционально: сортировка подходов в каждой группе по set_number (индекс 1)
    for key in grouped:
        grouped[key] = sorted(grouped[key], key=lambda x: x[1])
    return grouped


async def profile_trains_getter(dialog_manager: DialogManager, **_kwargs):
    tg_id = dialog_manager.event.from_user.id
    trains = await ProfileRepository.get_date_trains_profile(tg_id=tg_id)
    return {'trains': trains}


async def on_profile_trains_selected(callback: CallbackQuery, widget: Any,
                                     manager: DialogManager, selected_item: int):
    manager.dialog_data['selected_train'] = selected_item
    await manager.next()


async def profile_trains_data_getter(dialog_manager: DialogManager, **_kwargs):
    selected_train = dialog_manager.dialog_data['selected_train']
    tg_id = dialog_manager.event.from_user.id
    trains = await ProfileRepository.get_train_profile(tg_id, selected_train)
    grouped_trains = await group_trains_by_exercise(trains)
    return {'grouped_trains': grouped_trains}


main_profile_window = Window(
    Const('📊 <b>Ваш профиль</b>\n\n'
          'В данном окне вы можете посмотреть результаты тренировок согласно датам.'),
    Start(Const('Тренировки'), id='trains', state=states.Profile.TRAINS),
    # Start(Const('Упражнения'), id='exercises', state=states.Profile.EXERCISES),
    Start(Const('Назад'), id='__main__', state=states.Main.MAIN),
    state=states.Profile.MAIN
)

trains_profile_window = Window(
    Const('📅 <b>Даты ваших тренировок:</b>\n'),
    ScrollingGroup(Select(
        Jinja("{{ item.date.strftime('%d-%m-%Y - %A') | capitalize }}"),
        id='date',
        item_id_getter=operator.itemgetter(0),
        items='trains',
        on_click=on_profile_trains_selected
    ), width=1, height=8, id='list_trains'),
    Back(Const('Назад')),
    state=states.Profile.TRAINS,
    getter=profile_trains_getter
)

trains_data_profile_window = Window(
    Jinja("""
{% for exercise, details in grouped_trains.items() %}
🔹 <b>{{ exercise }}</b>
<blockquote>{% for train in details %}
   - Подход {{ train.set_number }}: {{ train.reps }}x{{ train.weight }} кг
{% endfor %}</blockquote>
{% endfor %}
    """),
    Back(Const('Назад')),
    state=states.Profile.TRAINS_INFO,
    getter=profile_trains_data_getter
)

exercises_profile_window = Window(
    Const('В данном окне вы можете посмотреть\n'),
    SwitchTo(Const('Назад'), id='back', state=states.Profile.MAIN),
    state=states.Profile.EXERCISES
)

profile_dialog = Dialog(
    main_profile_window,
    trains_profile_window,
    trains_data_profile_window,
)

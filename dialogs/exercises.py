from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import (ScrollingGroup, Back, SwitchTo,
                                        Select, Group, Start, Button)
from aiogram_dialog.widgets.text import Const, Format, Jinja
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog import ChatEvent

from aiogram.types import ContentType, Message, CallbackQuery
from aiogram import F
from typing import Any

from . import states
from db.requests import ExerciseRepository
from db.exercises_list import workout_plan


async def name_handler(message: Message, message_input: MessageInput,
                       manager: DialogManager):
    if manager.is_preview():
        await manager.next()
        return
    manager.dialog_data['exercise_name'] = message.text
    await manager.next()


async def other_type_handler(message: Message, message_input: MessageInput,
                             manager: DialogManager):
    await message.answer('Ваше сообщение совсем не похоже на текстовое!\n'
                         'Пожалуйста, повторите попытку.')


async def exercise_type_handler(callback: ChatEvent, select: Any,
                                manager: DialogManager, item_id: str):
    manager.dialog_data['exercise_type'] = item_id
    await ExerciseRepository.add_exercise(tg_id=manager.event.from_user.id,
                                          name=manager.dialog_data['exercise_name'],
                                          exercise_type=manager.dialog_data['exercise_type'])
    await manager.switch_to(state=states.Exercises.MAIN)


async def getter(dialog_manager: DialogManager, **_kwargs):
    exercises = await ExerciseRepository.list_exercises(tg_id=dialog_manager.event.from_user.id)
    return {'exercises': exercises}


async def on_exercise_selected(callback: CallbackQuery, widget: Any,
                               manager: DialogManager, selected_item: str):
    await callback.answer(selected_item)


async def on_edited_exercise_selected(callback: CallbackQuery, widget: Any,
                                      manager: DialogManager, selected_item: int):
    await ExerciseRepository.delete_exercise(tg_id=manager.event.from_user.id,
                                             exercise_id=selected_item)


async def default_exercises_getter(dialog_manager: DialogManager, **_kwargs):
    tg_id = dialog_manager.middleware_data['event_from_user'].id
    exercises = await ExerciseRepository.get_available_exercises(tg_id=tg_id)
    if exercises:
        return {'trains': False}
    return {'trains': True, 'workout_plan': workout_plan}


async def add_default_exercises_selected(callback: CallbackQuery, button: Button,
                                         manager: DialogManager):
    await ExerciseRepository.add_default_exercises(tg_id=manager.event.from_user.id, workout_plan=workout_plan)
    await manager.switch_to(state=states.Exercises.MAIN)


# region main window + add window
main_window = Window(
    Const('Меню управления тренировками'),
    Const('\nВы можете добавить стандартный список упражнений в меню "Упражнения по умолчанию"', when=F['trains']),
    SwitchTo(Const('Добавить упражнение'), id='add_exercise', state=states.Exercises.ADD_NAME),
    SwitchTo(Const('Редактировать упражнение'), id='edit_exercise', state=states.Exercises.EDIT),
    SwitchTo(Const('Список упражнений'), id='list_exercises', state=states.Exercises.LIST),
    SwitchTo(Const('Упражнения по умолчанию'),
             id='default_exercise',
             state=states.Exercises.DEFAULT_EXERCISE,
             when=F['trains']),
    Start(text=Const('Назад'), id="__main__", state=states.Main.MAIN),
    getter=default_exercises_getter,
    state=states.Exercises.MAIN
)
add_name_window = Window(
    Const('🏋️ <b>Добавление нового упражнения</b>\n\n'
          'Пожалуйста, введите название упражнения, которое вы хотите добавить в свой персональный план тренировок.\n\n'
          '🔤 <i>Пример</i>: Жим штанги лежа\n\n'
          'После ввода названия, я предложу вам выбрать группу мышц, для которых предназначено это упражнение.'
          ),
    MessageInput(name_handler, content_types=[ContentType.TEXT]),
    MessageInput(other_type_handler),
    SwitchTo(text=Const('Назад'), id='back', state=states.Exercises.MAIN),
    state=states.Exercises.ADD_NAME
)
add_type_window = Window(
    Const('Пожалуйста, выберите группу мышц, для которой предназначено упражнение:'),
    Group(Select(
        Format("{item}"),
        items=['Грудь', 'Спина', 'Плечи', 'Ноги', 'Руки', 'Прочее'],
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
    Const('🗑️ <b>Удаление упражнения</b>\n\n'
          'Выберите упражнение из списка ниже, которое вы хотите удалить.\n\n'
          '⚠️ <b>Внимание!</b> Удаление упражнения приведёт к потере всего связанного с ним прогресса!'),
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

default_exercises_window = Window(
    Jinja("""
<b>🏋️‍♂️ План тренировок 🏋️‍♀️</b>
{% for muscle_group, exercises in workout_plan.items() %}
<b>➡️ {{ muscle_group }}:</b>
<blockquote>{% for exercise in exercises %}
  • {{ exercise }}
{% endfor %}</blockquote>
{% if not loop.last %}
{% endif %}
{% endfor %}
    """),
    Button(text=Const('Добавить список упражнений'), id='ex_add', on_click=add_default_exercises_selected),
    SwitchTo(text=Const('Назад'), id='back', state=states.Exercises.MAIN),
    state=states.Exercises.DEFAULT_EXERCISE,
    getter=default_exercises_getter
)

exercises_dialog = Dialog(
    main_window,
    list_exercises_window,
    add_name_window,
    add_type_window,
    edit_exercise_window,
    default_exercises_window
)

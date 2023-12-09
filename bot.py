import asyncio
from asyncio import WindowsSelectorEventLoopPolicy
import logging

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import ExceptionTypeFilter
from aiogram.types import Message, ErrorEvent, ReplyKeyboardRemove
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.callback_answer import CallbackAnswerMiddleware
from aiogram.fsm.storage.memory import MemoryStorage

from aiogram_dialog import DialogManager, setup_dialogs, StartMode, ShowMode
from aiogram_dialog.api.exceptions import UnknownIntent


from config import config
from middlewares.db import DbSessionMiddleware
from db.models import sessionmaker, create_tables
from db.requests import UserRepository
from dialogs import states


from dialogs.main import main_dialog
from dialogs.exercises import exercises_dialog
from dialogs.trains import trains_dialog
from dialogs.information import info_dialog


logger = logging.getLogger(__name__)


async def start(message: Message, dialog_manager: DialogManager):
    if not await UserRepository.get_user(tg_id=message.from_user.id):
        await UserRepository.create_user(tg_id=message.from_user.id)
    await dialog_manager.start(states.Main.MAIN, mode=StartMode.RESET_STACK,
                               show_mode=ShowMode.EDIT)


async def on_unknown_intent(event: ErrorEvent, dialog_manager: DialogManager):
    logging.error('Restarting dialog: %s', event.exception)
    if event.update.callback_query:
        await event.update.callback_query.answer(
            "Бот был перезапущен в связи с техническим обслуживанием.\n"
            "Перенаправление в главное меню.",
        )
        if event.update.callback_query.message:
            try:
                await event.update.callback_query.message.delete()
            except TelegramBadRequest:
                pass
    elif event.update.message:
        await event.update.message.answer(
            "Процесс бота был перезапущен в связи с техническим обслуживанием.\n"
            "Перенаправление в главное меню.",
            reply_markup=ReplyKeyboardRemove(),
        )
    await dialog_manager.start(states.Main.MAIN, mode=StartMode.RESET_STACK,
                               show_mode=ShowMode.EDIT)


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    )
    logging.info('Starting bot')

    bot: Bot = Bot(token=config.bot_token.get_secret_value(), parse_mode='HTML')
    storage = MemoryStorage()
    dp: Dispatcher = Dispatcher(storage=storage)

    dp.update.middleware(DbSessionMiddleware(session_pool=sessionmaker))
    dialog_router = Router()
    dialog_router.include_routers(
        main_dialog,
        exercises_dialog,
        trains_dialog,
        info_dialog
    )

    dp.message.register(start, F.text == '/start')
    dp.errors.register(on_unknown_intent,
                       ExceptionTypeFilter(UnknownIntent))

    dp.include_router(dialog_router)
    setup_dialogs(dp)

    await create_tables()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    asyncio.run(main())


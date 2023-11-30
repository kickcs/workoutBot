import asyncio
from asyncio import WindowsSelectorEventLoopPolicy
import logging

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage


from config import config


logger = logging.getLogger(__name__)

async def cmd_start(message: Message):
    await message.answer('Hello!')


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    )
    logging.info('Starting bot')

    bot: Bot = Bot(token=config.bot_token.get_secret_value(), parse_mode='HTML')
    storage = MemoryStorage()
    dp: Dispatcher = Dispatcher(storage=storage)

    dp.message.register(cmd_start)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
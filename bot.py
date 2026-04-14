import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database import Database
from handlers import admin, menu, payment, start


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s: %(message)s",
    )

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    db = Database()
    await db.init()

    dp = Dispatcher(storage=MemoryStorage())

    # Router order matters: admin first so admin FSM states are matched first
    dp.include_router(admin.router)
    dp.include_router(payment.router)
    dp.include_router(start.router)
    dp.include_router(menu.router)

    logging.info("Bot ishga tushdi ✅")
    try:
        await dp.start_polling(bot, db=db)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

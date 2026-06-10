import asyncio
import logging

from aiogram import Bot, Dispatcher

from app.config import load_config
from app.database import init_db
from app.handlers import admin, user


config = load_config()


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    init_db()

    bot = Bot(token=config.bot_token)
    dp = Dispatcher()

    dp.include_router(user.router)
    dp.include_router(admin.router)

    await dp.start_polling(
        bot,
        config=config,
    )


if __name__ == "__main__":
    asyncio.run(main())
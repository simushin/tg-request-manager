import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from app.config import load_config
from app.database import init_db


config = load_config()


async def start_handler(message: Message) -> None:
    """
    Обработчик команды /start.
    Пока просто проверяем, что бот работает.
    """
    user_id = message.from_user.id

    text = (
        "Бот запущен.\n\n"
        "Это Telegram-бот для приема заявок.\n\n"
        f"Ваш Telegram ID: {user_id}"
    )

    await message.answer(text)


async def admin_handler(message: Message) -> None:
    """
    Обработчик команды /admin.
    Пока проверяем доступ администратора.
    """
    user_id = message.from_user.id

    if user_id != config.admin_id:
        await message.answer("У вас нет доступа к админ-панели.")
        return

    await message.answer("Админ-панель доступна. Позже здесь будет список заявок.")


async def main() -> None:
    """
    Точка входа в приложение.
    """
    logging.basicConfig(level=logging.INFO)

    init_db()

    bot = Bot(token=config.bot_token)
    dp = Dispatcher()

    dp.message.register(start_handler, CommandStart())
    dp.message.register(admin_handler, Command("admin"))

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
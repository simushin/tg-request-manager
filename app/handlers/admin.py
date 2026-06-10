from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.config import Config


router = Router()


@router.message(Command("admin"))
async def admin_handler(message: Message, config: Config) -> None:
    user_id = message.from_user.id

    if user_id != config.admin_id:
        await message.answer("У вас нет доступа к админ-панели.")
        return

    await message.answer(
        "Админ-панель доступна.\n"
        "Следующим шагом добавим просмотр заявок и смену статусов."
    )
import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.config import Config
from app.database import create_request
from app.keyboards import (
    CANCEL_BUTTON_TEXT,
    REQUEST_BUTTON_TEXT,
    get_cancel_keyboard,
    get_main_menu,
)
from app.states import RequestForm


router = Router()


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext) -> None:
    await state.clear()

    text = (
        "Здравствуйте.\n\n"
        "Это бот для приема заявок.\n"
        "Нажмите кнопку ниже, чтобы оставить заявку."
    )

    await message.answer(text, reply_markup=get_main_menu())


@router.message(Command("cancel"))
@router.message(F.text == CANCEL_BUTTON_TEXT)
async def cancel_handler(message: Message, state: FSMContext) -> None:
    await state.clear()

    await message.answer(
        "Действие отменено.",
        reply_markup=get_main_menu(),
    )


@router.message(F.text == REQUEST_BUTTON_TEXT)
async def start_request_form(message: Message, state: FSMContext) -> None:
    await state.set_state(RequestForm.full_name)

    await message.answer(
        "Введите ваше имя:",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(RequestForm.full_name)
async def process_full_name(message: Message, state: FSMContext) -> None:
    full_name = message.text.strip()

    if len(full_name) < 2:
        await message.answer("Имя слишком короткое. Введите имя еще раз:")
        return

    await state.update_data(full_name=full_name)
    await state.set_state(RequestForm.contact)

    await message.answer(
        "Введите контакт для связи.\n"
        "Например: номер телефона или username в Telegram."
    )


@router.message(RequestForm.contact)
async def process_contact(message: Message, state: FSMContext) -> None:
    contact = message.text.strip()

    if len(contact) < 3:
        await message.answer("Контакт слишком короткий. Введите контакт еще раз:")
        return

    await state.update_data(contact=contact)
    await state.set_state(RequestForm.subject)

    await message.answer("Введите тему заявки:")


@router.message(RequestForm.subject)
async def process_subject(message: Message, state: FSMContext) -> None:
    subject = message.text.strip()

    if len(subject) < 3:
        await message.answer("Тема слишком короткая. Введите тему еще раз:")
        return

    await state.update_data(subject=subject)
    await state.set_state(RequestForm.message)

    await message.answer("Опишите вашу заявку подробнее:")


@router.message(RequestForm.message)
async def process_request_message(
    message: Message,
    state: FSMContext,
    bot: Bot,
    config: Config,
) -> None:
    request_message = message.text.strip()

    if len(request_message) < 5:
        await message.answer("Описание слишком короткое. Опишите заявку подробнее:")
        return

    data = await state.get_data()

    username = message.from_user.username
    username_text = f"@{username}" if username else None

    request_id = create_request(
        username=username_text,
        full_name=data["full_name"],
        contact=data["contact"],
        subject=data["subject"],
        message=request_message,
    )

    await state.clear()

    await message.answer(
        f"Заявка №{request_id} принята.\n"
        "Администратор рассмотрит ее и свяжется с вами.",
        reply_markup=get_main_menu(),
    )

    admin_text = (
        f"Новая заявка №{request_id}\n\n"
        f"Имя: {data['full_name']}\n"
        f"Контакт: {data['contact']}\n"
        f"Telegram: {username_text or 'не указан'}\n"
        f"Тема: {data['subject']}\n\n"
        f"Описание:\n{request_message}"
    )

    try:
        await bot.send_message(
            chat_id=config.admin_id,
            text=admin_text,
        )
    except Exception:
        logging.exception("Не удалось отправить уведомление администратору")
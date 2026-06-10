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


def get_clean_text(message: Message) -> str | None:
    """
    Возвращает очищенный текст сообщения.
    Если пользователь отправил не текст, возвращает None.
    """
    if message.text is None:
        return None

    text = message.text.strip()

    if not text:
        return None

    return text


async def validate_text_input(
    message: Message,
    min_length: int,
    max_length: int,
    field_name: str,
) -> str | None:
    """
    Проверяет текстовое сообщение пользователя.
    Возвращает текст, если он корректный.
    Иначе отправляет пользователю сообщение об ошибке.
    """
    text = get_clean_text(message)

    if text is None:
        await message.answer(
            f"Пожалуйста, отправьте {field_name} обычным текстом."
        )
        return None

    if text.startswith("/"):
        await message.answer(
            "Сейчас идет заполнение заявки.\n"
            "Введите данные текстом или нажмите «Отмена»."
        )
        return None

    if len(text) < min_length:
        await message.answer(
            f"Слишком коротко. Введите {field_name} еще раз."
        )
        return None

    if len(text) > max_length:
        await message.answer(
            f"Слишком длинный текст. Максимум символов: {max_length}.\n"
            f"Введите {field_name} короче."
        )
        return None

    return text


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
    full_name = await validate_text_input(
        message=message,
        min_length=2,
        max_length=100,
        field_name="имя",
    )

    if full_name is None:
        return

    await state.update_data(full_name=full_name)
    await state.set_state(RequestForm.contact)

    await message.answer(
        "Введите контакт для связи.\n"
        "Например: номер телефона или username в Telegram."
    )


@router.message(RequestForm.contact)
async def process_contact(message: Message, state: FSMContext) -> None:
    contact = await validate_text_input(
        message=message,
        min_length=3,
        max_length=100,
        field_name="контакт",
    )

    if contact is None:
        return

    await state.update_data(contact=contact)
    await state.set_state(RequestForm.subject)

    await message.answer("Введите тему заявки:")


@router.message(RequestForm.subject)
async def process_subject(message: Message, state: FSMContext) -> None:
    subject = await validate_text_input(
        message=message,
        min_length=3,
        max_length=150,
        field_name="тему заявки",
    )

    if subject is None:
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
    request_message = await validate_text_input(
        message=message,
        min_length=5,
        max_length=1000,
        field_name="описание заявки",
    )

    if request_message is None:
        return

    data = await state.get_data()

    username = message.from_user.username
    username_text = f"@{username}" if username else None

    try:
        request_id = create_request(
            username=username_text,
            full_name=data["full_name"],
            contact=data["contact"],
            subject=data["subject"],
            message=request_message,
        )
    except Exception:
        logging.exception("Не удалось сохранить заявку в базу данных")

        await message.answer(
            "Произошла ошибка при сохранении заявки.\n"
            "Попробуйте отправить заявку позже.",
            reply_markup=get_main_menu(),
        )

        await state.clear()
        return

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
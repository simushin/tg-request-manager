from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from app.config import Config
from app.database import (
    export_requests_to_csv,
    get_last_requests,
    get_request_by_id,
    update_request_status,
)


router = Router()


STATUS_LABELS = {
    "new": "Новая",
    "in_work": "В работе",
    "closed": "Закрыта",
}


def get_admin_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Последние заявки",
                    callback_data="admin:last",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Экспорт CSV",
                    callback_data="admin:export",
                )
            ],
        ]
    )


def get_requests_list_keyboard(requests: list[dict]) -> InlineKeyboardMarkup:
    keyboard = []

    for request in requests:
        request_id = request["id"]
        subject = request["subject"]
        status = STATUS_LABELS.get(request["status"], request["status"])

        if len(subject) > 25:
            subject = subject[:25] + "..."

        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"№{request_id} | {status} | {subject}",
                    callback_data=f"request:view:{request_id}",
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                text="Назад",
                callback_data="admin:menu",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_request_actions_keyboard(request_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="В работу",
                    callback_data=f"request:status:{request_id}:in_work",
                ),
                InlineKeyboardButton(
                    text="Закрыть",
                    callback_data=f"request:status:{request_id}:closed",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Назад к списку",
                    callback_data="admin:last",
                )
            ],
        ]
    )


def format_request(request: dict) -> str:
    status = STATUS_LABELS.get(request["status"], request["status"])

    username = request["username"] or "не указан"

    return (
        f"Заявка №{request['id']}\n\n"
        f"Статус: {status}\n"
        f"Дата: {request['created_at']}\n\n"
        f"Имя: {request['full_name']}\n"
        f"Контакт: {request['contact']}\n"
        f"Telegram: {username}\n\n"
        f"Тема: {request['subject']}\n\n"
        f"Описание:\n{request['message']}"
    )


@router.message(Command("admin"))
async def admin_handler(message: Message, config: Config) -> None:
    user_id = message.from_user.id

    if user_id != config.admin_id:
        await message.answer("У вас нет доступа к админ-панели.")
        return

    await message.answer(
        "Админ-панель",
        reply_markup=get_admin_menu_keyboard(),
    )


@router.callback_query(F.data == "admin:menu")
async def admin_menu_callback(callback: CallbackQuery, config: Config) -> None:
    if callback.from_user.id != config.admin_id:
        await callback.answer("Нет доступа.", show_alert=True)
        return

    await callback.message.edit_text(
        "Админ-панель",
        reply_markup=get_admin_menu_keyboard(),
    )

    await callback.answer()


@router.callback_query(F.data == "admin:last")
async def last_requests_callback(callback: CallbackQuery, config: Config) -> None:
    if callback.from_user.id != config.admin_id:
        await callback.answer("Нет доступа.", show_alert=True)
        return

    requests = get_last_requests(limit=10)

    if not requests:
        await callback.message.edit_text(
            "Заявок пока нет.",
            reply_markup=get_admin_menu_keyboard(),
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        "Последние заявки:",
        reply_markup=get_requests_list_keyboard(requests),
    )

    await callback.answer()


@router.callback_query(F.data.startswith("request:view:"))
async def view_request_callback(callback: CallbackQuery, config: Config) -> None:
    if callback.from_user.id != config.admin_id:
        await callback.answer("Нет доступа.", show_alert=True)
        return

    request_id = int(callback.data.split(":")[2])

    request = get_request_by_id(request_id)

    if request is None:
        await callback.answer("Заявка не найдена.", show_alert=True)
        return

    await callback.message.edit_text(
        format_request(request),
        reply_markup=get_request_actions_keyboard(request_id),
    )

    await callback.answer()


@router.callback_query(F.data.startswith("request:status:"))
async def change_request_status_callback(
    callback: CallbackQuery,
    config: Config,
) -> None:
    if callback.from_user.id != config.admin_id:
        await callback.answer("Нет доступа.", show_alert=True)
        return

    _, _, request_id_text, status = callback.data.split(":")
    request_id = int(request_id_text)

    updated = update_request_status(request_id, status)

    if not updated:
        await callback.answer("Заявка не найдена.", show_alert=True)
        return

    request = get_request_by_id(request_id)

    await callback.message.edit_text(
        format_request(request),
        reply_markup=get_request_actions_keyboard(request_id),
    )

    await callback.answer("Статус обновлен.")


@router.callback_query(F.data == "admin:export")
async def export_csv_callback(callback: CallbackQuery, config: Config) -> None:
    if callback.from_user.id != config.admin_id:
        await callback.answer("Нет доступа.", show_alert=True)
        return

    csv_path = export_requests_to_csv()

    await callback.message.answer_document(
        FSInputFile(csv_path),
        caption="Экспорт заявок в CSV",
    )

    await callback.answer()
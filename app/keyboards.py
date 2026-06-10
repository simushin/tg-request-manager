from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


REQUEST_BUTTON_TEXT = "Оставить заявку"
CANCEL_BUTTON_TEXT = "Отмена"


def get_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=REQUEST_BUTTON_TEXT)],
        ],
        resize_keyboard=True,
    )


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=CANCEL_BUTTON_TEXT)],
        ],
        resize_keyboard=True,
    )
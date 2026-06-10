from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"


@dataclass(frozen=True)
class Config:
    bot_token: str
    admin_id: int


def load_config() -> Config:
    """
    Загружает настройки проекта из файла .env.
    """
    load_dotenv(ENV_PATH)

    bot_token = os.getenv("BOT_TOKEN")
    admin_id = os.getenv("ADMIN_ID")

    if not bot_token:
        raise RuntimeError("Не указан BOT_TOKEN в файле .env")

    if not admin_id:
        raise RuntimeError("Не указан ADMIN_ID в файле .env")

    try:
        admin_id_int = int(admin_id)
    except ValueError:
        raise RuntimeError("ADMIN_ID должен быть числом")

    return Config(
        bot_token=bot_token,
        admin_id=admin_id_int,
    )
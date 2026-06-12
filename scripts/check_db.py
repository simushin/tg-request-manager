import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "requests.db"


def main() -> None:
    if not DB_PATH.exists():
        print(f"Файл базы данных не найден: {DB_PATH}")
        return

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            """
            SELECT
                id,
                username,
                full_name,
                contact,
                subject,
                message,
                status,
                created_at
            FROM requests
            ORDER BY id DESC
            """
        ).fetchall()

    if not rows:
        print("Заявок пока нет.")
        return

    for row in rows:
        print("-" * 50)
        print(f"ID: {row['id']}")
        print(f"Username: {row['username'] or 'не указан'}")
        print(f"Имя: {row['full_name']}")
        print(f"Контакт: {row['contact']}")
        print(f"Тема: {row['subject']}")
        print(f"Сообщение: {row['message']}")
        print(f"Статус: {row['status']}")
        print(f"Создана: {row['created_at']}")


if __name__ == "__main__":
    main()
from pathlib import Path
import sqlite3
import csv
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
EXPORT_DIR = BASE_DIR / "exports"

DB_PATH = DATA_DIR / "requests.db"

VALID_STATUSES = {"new", "in_work", "closed"}


def get_connection() -> sqlite3.Connection:
    """
    Создает подключение к SQLite.
    Если папки data еще нет, она будет создана автоматически.
    """
    DATA_DIR.mkdir(exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    return conn


def init_db() -> None:
    """
    Создает таблицу заявок, если она еще не существует.
    """
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                full_name TEXT NOT NULL,
                contact TEXT NOT NULL,
                subject TEXT NOT NULL,
                message TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'new',
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def create_request(
    username: str | None,
    full_name: str,
    contact: str,
    subject: str,
    message: str,
) -> int:
    """
    Создает новую заявку и возвращает ее ID.
    """
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO requests (
                username,
                full_name,
                contact,
                subject,
                message,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                username,
                full_name,
                contact,
                subject,
                message,
                "new",
                created_at,
            ),
        )
        conn.commit()

        return cursor.lastrowid


def get_request_by_id(request_id: int) -> dict | None:
    """
    Возвращает заявку по ID.
    Если заявки нет, возвращает None.
    """
    with get_connection() as conn:
        row = conn.execute(
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
            WHERE id = ?
            """,
            (request_id,),
        ).fetchone()

    if row is None:
        return None

    return dict(row)


def get_last_requests(limit: int = 10) -> list[dict]:
    """
    Возвращает последние заявки.
    По умолчанию — 10 последних.
    """
    with get_connection() as conn:
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
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]


def update_request_status(request_id: int, status: str) -> bool:
    """
    Обновляет статус заявки.
    Возвращает True, если заявка была найдена и обновлена.
    """
    if status not in VALID_STATUSES:
        raise ValueError(f"Недопустимый статус: {status}")

    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE requests
            SET status = ?
            WHERE id = ?
            """,
            (status, request_id),
        )
        conn.commit()

        return cursor.rowcount > 0


def export_requests_to_csv() -> Path:
    """
    Выгружает все заявки в CSV-файл.
    Возвращает путь к созданному файлу.
    """
    EXPORT_DIR.mkdir(exist_ok=True)

    export_path = EXPORT_DIR / "requests.csv"

    with get_connection() as conn:
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

    with open(export_path, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)

        writer.writerow(
            [
                "id",
                "username",
                "full_name",
                "contact",
                "subject",
                "message",
                "status",
                "created_at",
            ]
        )

        for row in rows:
            writer.writerow(
                [
                    row["id"],
                    row["username"],
                    row["full_name"],
                    row["contact"],
                    row["subject"],
                    row["message"],
                    row["status"],
                    row["created_at"],
                ]
            )

    return export_path


if __name__ == "__main__":
    init_db()

    request_id = create_request(
        username="test_user",
        full_name="Иван Иванов",
        contact="@test_user",
        subject="Тестовая заявка",
        message="Проверка работы базы данных.",
    )

    print(f"Создана заявка ID: {request_id}")

    request_data = get_request_by_id(request_id)
    print("Заявка:")
    print(request_data)

    update_request_status(request_id, "in_work")
    print("Статус изменен на in_work")

    last_requests = get_last_requests()
    print("Последние заявки:")
    print(last_requests)

    csv_path = export_requests_to_csv()
    print(f"CSV-файл создан: {csv_path}")
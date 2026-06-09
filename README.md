# tg-request-manager

Telegram-бот для приема и обработки заявок.

## Возможности

- прием заявок от пользователей;
- пошаговая форма заявки;
- сохранение заявок в SQLite;
- уведомление администратора;
- админ-панель внутри Telegram;
- смена статусов заявок;
- экспорт заявок в CSV.

## Стек

- Python
- aiogram
- SQLite
- python-dotenv

## Настройка

Создайте файл `.env` на основе `.env.example`:

```env
BOT_TOKEN=your_bot_token_here
ADMIN_ID=123456789
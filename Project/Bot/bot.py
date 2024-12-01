from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command
from datetime import datetime, timedelta
import asyncio
import logging

from Database import ClientsDB, Errors
from GPT_Parser.GPT_parser import GPTParser
from Calendar.Calendar_module import CalendarModule
from Notion.notion_api import add_task_to_notion  # Предполагаем, что вы создали `notion_api.py`

# Установите свой токен Telegram
API_TOKEN = "ВАШ_ТЕЛЕГРАМ_ТОКЕН"

# Логирование
logging.basicConfig(level=logging.INFO)

# Создаём объект бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()

# Инициализация базы данных, GPT-парсера, Google Calendar и Notion
db = ClientsDB()  # Подключаем базу данных
gpt_parser = GPTParser()  # GPT-парсер для обработки сообщений
calendar = CalendarModule()  # Google Calendar

# Простая структура для временного хранения ожидаемых событий
pending_events = {}

# --- Обработчики команд ---

@router.message(Command("start"))
async def start_handler(message: types.Message):
    """
    Обрабатывает команду /start.
    Регистрирует пользователя в базе данных, если он ещё не зарегистрирован.
    """
    telegram_id = str(message.from_user.id)
    user_calendar_id = db.get_calendar_id(telegram_id)

    if user_calendar_id:  # Если пользователь уже зарегистрирован
        await message.answer("Вы уже зарегистрированы. Можете начинать отправлять запросы!")
    else:
        db.add_client(telegram_id, google_calendar_id="", notion_id="")
        await message.answer(
            "Привет! Для начала работы введите ссылки на ваш Google Calendar и Notion.\n\n"
            "Пример: \n"
            "`https://calendar.google.com` и `https://www.notion.so`",
            parse_mode="Markdown"
        )


@router.message()
async def save_links_handler(message: types.Message):
    """
    Сохраняет ссылки, введённые пользователем, в базу данных.
    """
    telegram_id = str(message.from_user.id)
    user_calendar_id = db.get_calendar_id(telegram_id)
    user_notion_id = db.get_notion_id(telegram_id)

    if not user_calendar_id[0]:  # Если ссылка на календарь не указана
        if not message.text.startswith("https://"):
            await message.answer("Это не похоже на ссылку. Попробуйте снова.")
            return
        db.add_client(telegram_id, google_calendar_id=message.text, notion_id=user_notion_id[0])
        await message.answer("Ссылка на календарь сохранена! Теперь введите ссылку на ваш Notion.")
    elif not user_notion_id[0]:  # Если ссылка на Notion не указана
        if not message.text.startswith("https://"):
            await message.answer("Это не похоже на ссылку. Попробуйте снова.")
            return
        db.add_client(telegram_id, google_calendar_id=user_calendar_id[0], notion_id=message.text)
        await message.answer("Ссылка на Notion сохранена! Вы готовы к работе.")
    else:
        await message.answer("Все данные уже сохранены. Вы можете отправлять запросы!")


@router.message()
async def event_handler(message: types.Message):
    """
    Передаёт сообщение пользователя GPT-парсеру для извлечения информации о событии.
    """
    telegram_id = str(message.from_user.id)
    user_calendar_id = db.get_calendar_id(telegram_id)

    if not user_calendar_id[0]:  # Если пользователь не настроил календарь
        await message.answer("Пожалуйста, сначала настройте Google Calendar с помощью команды /start.")
        return

    try:
        # Парсим сообщение через GPT-парсер
        parsed_event = gpt_parser.parse(message.text)
        event_datetime = datetime.fromisoformat(parsed_event["datetime"])
        pending_events[telegram_id] = {
            "title": parsed_event["title"],
            "datetime": event_datetime,
            "location": parsed_event.get("location", "Не указано"),
        }

        # Уточняем информацию у пользователя
        await message.answer(
            f"Вы хотите запланировать '{parsed_event['title']}' на {event_datetime.strftime('%d.%m.%Y %H:%M')} "
            f"в месте: {parsed_event.get('location', 'Не указано')}?"
            "\n\nОтветьте 'да' для подтверждения или отправьте новое сообщение для изменения."
        )
    except Exception as e:
        await message.answer("Не удалось распознать событие. Попробуйте ещё раз.")
        logging.error(f"Ошибка парсинга: {e}")


@router.message()
async def confirm_event_handler(message: types.Message):
    """
    Подтверждает событие и создаёт его в Google Calendar и Notion.
    """
    telegram_id = str(message.from_user.id)

    if telegram_id not in pending_events:  # Если нет ожидающих подтверждения событий
        await message.answer("Нет ожидающих подтверждения событий.")
        return

    if message.text.lower() == "да":  # Пользователь подтверждает событие
        event = pending_events[telegram_id]
        calendar_event = {
            "summary": event["title"],
            "start": {"dateTime": event["datetime"].isoformat()},
            "end": {"dateTime": (event["datetime"] + timedelta(hours=1)).isoformat()},
            "location": event["location"],
        }

        # Создаём событие в Google Calendar
        db_calendar_id = db.get_calendar_id(telegram_id)[0]  # Получаем ID календаря
        calendar.create_event(calendar_event, db_calendar_id)

        # Создаём задачу в Notion
        notion_database_id = db.get_notion_id(telegram_id)[0]
        add_task_to_notion(
            database_id=notion_database_id,
            task_name=event["title"],
            task_due_date=event["datetime"].strftime('%Y-%m-%d')
        )

        await message.answer(f"Событие '{event['title']}' добавлено в Google Calendar и Notion.")
        del pending_events[telegram_id]  # Удаляем временные данные
    else:
        await message.answer("Событие отменено.")
        del pending_events[telegram_id]


async def main():
    """
    Запускает бота.
    """
    logging.info("Бот запущен!")
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

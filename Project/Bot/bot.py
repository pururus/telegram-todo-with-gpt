import notion
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import asyncio

from Project.Database import ClientsDB, Errors
from Project.Calendar.Calendar_module import CalendarModule
from Project.API_notion.Notion_module import NotionModule




API_TOKEN = "8149845915:AAEoY53NSKqO5QntlTI6fwz4x-0j70e1X3o"

# Создаём объект бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()

# Инициализация базы данных, Google Calendar и Notion
db = ClientsDB()  # Подключаем базу данных
calendar = CalendarModule()  # Google Calendar

# Простая структура для временного хранения ожидаемых событий
pending_events = {}

# Заглушка для GPT Parser
def mock_gpt_parser(message_text: str) -> dict:
    """
    Временная заглушка для GPT-парсера.
    Анализирует текст сообщения и возвращает фиктивные данные о событии.
    """
    if "завтра" in message_text.lower():
        event_datetime = datetime.now() + timedelta(days=1)
    else:
        event_datetime = datetime.now()

    return {
        "title": "Пример события",
        "datetime": event_datetime.isoformat(),
        "location": "Не указано",
    }


# Кнопки выбора действия
def get_main_menu_buttons():
    """
    Создаёт кнопки для выбора действия (добавление задачи или события).
    """
    buttons = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Добавить задачу", callback_data="add_task"),
                InlineKeyboardButton(text="Добавить событие", callback_data="add_event"),
            ]
        ]
    )
    return buttons


# Обработчик команды /start
@router.message(Command("start"))
async def start_handler(message: types.Message):
    """
    Обрабатывает команду /start.
    Показывает меню выбора действия.
    """
    telegram_id = str(message.from_user.id)
    user_calendar_id = db.get_calendar_id(telegram_id)

    if user_calendar_id:  # Если пользователь уже зарегистрирован
        await message.answer("Выбирай епта:", reply_markup=get_main_menu_buttons())
    else:
        # Регистрируем нового пользователя
        db.add_client(telegram_id, google_calendar_id="", notion_id="", notion_api_token="")
        await message.answer(
            "Привет! Для начала работы введите ссылки на ваш Google Calendar и Notion.\n\n"
            "Пример: \n"
            "`https://calendar.google.com` и `https://www.notion.so`",
            parse_mode="Markdown"
        )


# Обработчик для Inline кнопок
@router.callback_query()
async def handle_menu_selection(callback_query: types.CallbackQuery):
    """
    Обрабатывает нажатия на кнопки выбора действия.
    """
    telegram_id = str(callback_query.from_user.id)
    action = callback_query.data

    if action == "add_task":
        await callback_query.message.answer("Введите задачу для добавления в Notion.")
    elif action == "add_event":
        await callback_query.message.answer("Введите событие для добавления в Google Calendar.")
    else:
        await callback_query.message.answer("Неизвестное действие.")


# Обработчик для добавления задачи в Notion
@router.message(lambda message: message.text.startswith("Задача:"))
async def add_task_to_notion_handler(message: types.Message):
    """
    Добавляет задачу в базу данных Notion.
    """
    telegram_id = str(message.from_user.id)
    notion_token = db.get_notion_api_token(telegram_id)

    if not notion_token:
        await message.answer("Вы не настроили доступ к Notion. Введите ваш токен с помощью команды:\n"
                             "`notion_api_token: ваш_токен`", parse_mode="Markdown")
        return

    # Подключаемся к Notion с токеном пользователя
    notion = NotionModule(api_token=notion_token)
    notion_database_id = db.get_notion_id(telegram_id)

    if not notion_database_id:
        await message.answer("Вы не указали базу данных Notion блять. Отправьте ссылку на неё.")
        return

    task_title = message.text.replace("Задача:", "").strip()
    response = notion.create_task(
        database_id=notion_database_id,
        title=task_title,
        description="Описание задачи (можно заменить)",
        due_date=datetime.now().isoformat()
    )

    if response.get("success"):
        await message.answer(f"Задача '{task_title}' успешно добавлена в Notion.")
    else:
        await message.answer("Не удалось добавить задачу в Notion. Попробуйте ещё раз.")


# Обработчик для добавления события в Google Calendar
@router.message(lambda message: message.text.startswith("Событие:"))
async def add_event_to_calendar_handler(message: types.Message):
    """
    Добавляет событие в Google Calendar.
    """
    telegram_id = str(message.from_user.id)
    user_calendar_id = db.get_calendar_id(telegram_id)

    if not user_calendar_id[0]:
        await message.answer("Вы не настроили Google Calendar. Укажите ссылку через команду /start.")
        return

    parsed_event = mock_gpt_parser(message.text.replace("Событие:", "").strip())
    event_datetime = datetime.fromisoformat(parsed_event["datetime"])
    event = {
        "summary": parsed_event["title"],
        "start": {"dateTime": event_datetime.isoformat()},
        "end": {"dateTime": (event_datetime + timedelta(hours=1)).isoformat()},
        "location": parsed_event["location"],
    }

    response = calendar.create_event(event, user_calendar_id[0])
    if isinstance(response, dict) and "id" in response:
        await message.answer(f"Событие '{parsed_event['title']}' успешно добавлено в Google Calendar.")
    else:
        await message.answer("Не удалось добавить событие в Google Calendar. Попробуйте ещё раз.")


# Главная функция для запуска бота
async def main():
    """
    Запускает бота.
    """
    print("Бот запущен!")
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

# Запуск бота
if __name__ == "__main__":
    asyncio.run(main())

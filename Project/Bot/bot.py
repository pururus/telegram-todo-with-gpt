from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command
from datetime import datetime, timedelta
import asyncio

from Database import ClientsDB, Errors
from Calendar.Calendar_module import CalendarModule
from Notion.Notion_module import NotionModule 

API_TOKEN = "8149845915:AAEoY53NSKqO5QntlTI6fwz4x-0j70e1X3o"

# Создаём объект бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()

# Инициализация базы данных, Google Calendar и Notion
db = ClientsDB()  # Подключаем базу данных
calendar = CalendarModule()  # Google Calendar
# Notion будет инициализироваться динамически для каждого пользователя

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
        "title": "Пример события",  # Фиктивное название события
        "datetime": event_datetime.isoformat(),  # Текущая дата или дата завтра
        "location": "Не указано",  # Заглушка для места
    }

# Обработчик команды /start
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
        # Регистрируем нового пользователя
        db.add_client(telegram_id, google_calendar_id="", notion_id="", notion_api_token="")
        await message.answer(
            "Привет! Для начала работы введите ссылки на ваш Google Calendar и Notion.\n\n"
            "Пример: \n"
            "`https://calendar.google.com` и `https://www.notion.so`",
            parse_mode="Markdown"
        )

# Обработчик для сохранения ссылок и токена Notion
@router.message()
async def save_links_handler(message: types.Message):
    """
    Сохраняет ссылки, введённые пользователем, в базу данных.
    """
    telegram_id = str(message.from_user.id)
    user_calendar_id = db.get_calendar_id(telegram_id)
    user_notion_id = db.get_notion_id(telegram_id)

    if message.text.startswith("notion_api_token:"):
        notion_token = message.text.split(":", 1)[1].strip()
        db.update_client_notion_token(telegram_id, notion_token)  # Сохраняем токен в базу
        await message.answer("Ваш токен Notion сохранён. Вы готовы к работе!")
    elif not user_calendar_id[0]:  # Если ссылка на календарь не указана
        db.add_client(telegram_id, google_calendar_id=message.text, notion_id=user_notion_id[0])
        await message.answer("Ссылка на календарь сохранена! Теперь введите ссылку на ваш Notion.")
    elif not user_notion_id[0]:  # Если ссылка на Notion не указана
        db.update_client_notion_id(telegram_id, message.text)  # Сохраняем ссылку базы данных
        await message.answer("Ссылка на Notion сохранена! Теперь введите ваш токен Notion.\n"
                             "Пример: `notion_api_token: ваш_токен`", parse_mode="Markdown")
    else:
        await message.answer("Все данные уже сохранены. Вы можете отправлять запросы!")

# Обработчик для добавления задачи в Notion
@router.message(Command("add_task"))
async def add_task_to_notion_handler(message: types.Message):
    """
    Добавляет задачу в базу данных Notion.
    """
    telegram_id = str(message.from_user.id)
    notion_token = db.get_notion_api_token(telegram_id)  # Извлекаем токен пользователя

    if not notion_token:
        await message.answer("Вы не настроили доступ к Notion. Введите ваш токен с помощью команды:\n"
                             "`notion_api_token: ваш_токен`", parse_mode="Markdown")
        return

    # Подключаемся к Notion с токеном пользователя
    notion = NotionModule(api_token=notion_token)
    notion_database_id = db.get_notion_id(telegram_id)  # Получаем ID базы данных Notion

    if not notion_database_id:
        await message.answer("Вы не указали базу данных Notion. Отправьте ссылку на неё.")
        return

    # Получаем текст задачи от пользователя
    task_title = message.text.strip()
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

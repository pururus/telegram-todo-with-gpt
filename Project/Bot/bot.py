from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
from aiogram.types import FSInputFile
from datetime import datetime
import logging

"""
Настройка логирования:
Устанавливаем уровень логирования на INFO, чтобы видеть сообщения об основном ходе выполнения.
"""
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from pathlib import Path

search_directory = Path('../')
for file_path in search_directory.rglob("Project"):
    project = file_path.resolve()

import sys
sys.path.append('project')

from Todoist.Todoist_module import TodoistModule
from Database.Database import ClientsDB, Errors
from Calendar.Calendar_module import CalendarModule
from GPT.GPT_module import GPT
from Request import RequestType
from Query import Query
from GPT.credentials import cal_credentials

API_TOKEN = '8149845915:AAEoY53NSKqO5QntlTI6fwz4x-0j70e1X3o'

"""
Создаём объекты бота и диспетчера.
- Bot: для отправки и получения сообщений.
- Dispatcher: отвечает за маршрутизацию сообщений к нужным обработчикам.
"""
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

"""
Инициализация базы данных, CalendarModule и GPT:
- db: для работы с локальной БД (sqlite3)
- calendar: для взаимодействия с Google Calendar
- gpt_parser: для парсинга сообщений с помощью GPT
"""
db = ClientsDB("client_DB_____")
calendar = CalendarModule()
gpt_parser = GPT()

"""
Определение состояний:
- RegistrationStates: используются при начальной регистрации пользователя.
- UserStates: состояния при добавлении события или задачи.
- UpdateStates: используются при обновлении идентификаторов (Calendar ID, Todoist токен).
"""
class RegistrationStates(StatesGroup):
    waiting_for_google_calendar_id = State()
    waiting_for_todoist_token = State()

class UserStates(StatesGroup):
    waiting_for_event = State()
    waiting_for_task = State()

class UpdateStates(StatesGroup):
    waiting_for_new_calendar_id = State()
    waiting_for_new_todoist_token = State()

def get_main_menu_keyboard() -> types.ReplyKeyboardMarkup:
    """
    Создаёт клавиатуру с кнопками для главного меню.

    Returns:
        types.ReplyKeyboardMarkup: Разметка клавиатуры, содержащая две кнопки:
        - "Добавить событие"
        - "Добавить задачу"
    """
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton(text="Добавить событие"),
                types.KeyboardButton(text="Добавить задачу")
            ]
        ],
        resize_keyboard=True
    )
    return keyboard

def is_user_registered(telegram_id: str) -> bool:
    """
    Проверяет, есть ли у пользователя (telegram_id) в БД данные
    для Google Calendar и Todoist.

    Args:
        telegram_id (str): Telegram ID пользователя.
    Returns:
        bool: True, если и calendar_id, и todoist_token найдены, иначе False.
    """
    calendar_id = db.get_calendar_id(telegram_id)
    todoist_token = db.get_todoist_token(telegram_id)
    return bool(calendar_id and todoist_token)

@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    """
    Обработчик команды /start.

    Логика:
    1) Проверяем, зарегистрирован ли пользователь, обратившись к БД (is_user_registered).
    2) Если зарегистрирован, предлагаем главное меню.
    3) Иначе отправляем инструкцию по настройке Google Calendar и переводим бота в состояние ожидания Google Calendar ID.
    """
    telegram_id = str(message.from_user.id)

    if is_user_registered(telegram_id):
        await message.answer("Вы уже зарегистрированы.", reply_markup=get_main_menu_keyboard())
    else:
        calendar_image = FSInputFile("/Users/svatoslavpolonskiy/Documents/Deep_python/telegram-todo-with-gpt/Project/Bot/google_png.png")
        await message.answer_photo(
            photo=calendar_image,
            caption=(
                "🐠 Hello and Welcome! 🐟\n\n"
                "Для начала работы мне понадобятся некоторые данные:\n\n"
                "🐠 Шаг 1: Настройка Google Calendar 🐠\n\n"
                "Следуйте инструкции на изображении:\n"
                "1️⃣ Откройте настройки Google Календаря.\n"
                "2️⃣ Выберите нужный календарь.\n"
                "3️⃣ Перейдите в раздел Интеграция календаря.\n"
                "4️⃣ Скопируйте ID календаря.\n"
                "5️⃣ Откройте доступ на редактирование для адреса:\n"
                "   to-do-with-gpt-project@to-do-443214.iam.gserviceaccount.com.\n\n"
                "📤 Отправьте скопированный Google Calendar ID в ответ на это сообщение."
            ),
            parse_mode="Markdown"
        )
        await state.set_state(RegistrationStates.waiting_for_google_calendar_id)

@dp.message(Command("info"))
async def info_handler(message: types.Message):
    """
    Обработчик команды /info.

    Показывает список доступных команд бота, чтобы пользователь мог быстро ознакомиться с функционалом.
    """
    info_message = (
        "📘 **Доступные команды бота:**\n\n"
        "/start - начать работу с ботом и зарегистрироваться \n"
        "/unreg - удалить свои данные и отменить регистрацию :(\n"
        "/update_calendar - обновить Google Calendar ID\n"
        "/update_todoist - обновить Todoist API токен\n"
        "/status - проверить текущие идентификаторы (Google Calendar ID и Todoist API токен)\n"
        "/info - посмотреть команды бота\n"
        "Добавить событие - создать событие в Google Calendar\n"
        "Добавить задачу - создать задачу в Todoist\n\n"
        "Такие дела. 📖"
    )
    await message.answer(info_message, parse_mode="Markdown")

@dp.message(RegistrationStates.waiting_for_google_calendar_id)
async def process_google_calendar_id(message: types.Message, state: FSMContext):
    """
    Обрабатывает получение Google Calendar ID.

    1) Проверяет валидность календаря (validate_calendar_id).
    2) Если неверно — просит повторить ввод.
    3) Если верно — переходим к запросу Todoist токена.
    """
    google_calendar_id = message.text.strip()
    telegram_id = str(message.from_user.id)

    is_valid = calendar.validate_calendar_id(google_calendar_id)
    if not is_valid:
        await message.answer_sticker("CAACAgIAAxkBAAENXVVnZpAk9PS1lNx4P-nqpTvDiFaDaQACt2IAA7QwSwxxEbxXoU5MNgQ") # неверный гугол календарь айди
        return

    await state.update_data(google_calendar_id=google_calendar_id)

    todoist_image = FSInputFile("/Users/svatoslavpolonskiy/Documents/Deep_python/telegram-todo-with-gpt/Project/Bot/todoist_png.png")
    await message.answer_photo(
        photo=todoist_image,
        caption=(
            "Супер!🐬\n\n"
            "🐠**Шаг 2: Настройка Todoist API токена**🐳\n\n"
            "Следуйте инструкции на изображении:\n"
            "1️⃣ Откройте настройки вашего Todoist аккаунта.\n"
            "2️⃣ Перейдите в раздел **Интеграции** или **API токены**.\n"
            "3️⃣ Выберите раздел **Developer**.\n"
            "4️⃣ Скопируйте ваш **API токен**.\n\n"
            "📤 Отправьте скопированный **Todoist API токен** в ответ на это сообщение."
        ),
        parse_mode="Markdown"
    )
    await state.set_state(RegistrationStates.waiting_for_todoist_token)

@dp.message(RegistrationStates.waiting_for_todoist_token)
async def process_todoist_token(message: types.Message, state: FSMContext):
    """
    Обрабатывает получение токена Todoist.

    1) Проверяем валидность Todoist токена (validate_token).
    2) Если неверно — отправляем стикер.
    3) Если верно — сохраняем данные в БД и завершаем регистрацию.
    """
    todoist_token = message.text.strip()
    telegram_id = str(message.from_user.id)

    data = await state.get_data()
    google_calendar_id = data.get('google_calendar_id')

    try:
        # Инициализация модуля Todoist
        todoist_module = TodoistModule(todoist_token)

        # Проверка валидности токена
        if not todoist_module.validate_token():
            # Если токен невалидный, отправляем стикер
            await message.answer_sticker("CAACAgIAAxkBAAENXVlnZpBVoCDz9AbxflDAeW1KWVXSCAACuWEAAq-EMUuLDDAtDmQyNzYE")  # Стикер с сообщением о неверном токене
            return
    except Exception as e:
        logger.error(f"Ошибка при валидации токена: {e}")
        # Отправляем стикер при любой ошибке
        await message.answer_sticker("CAACAgIAAxkBAAENXVlnZpBVoCDz9AbxflDAeW1KWVXSCAACuWEAAq-EMUuLDDAtDmQyNzYE")
        return

    # Если токен валидный, продолжаем регистрацию
    result = db.add_client(telegram_id, google_calendar_id, todoist_token)
    if result == Errors.INTEGRITY_ERROR.value:
        await message.answer("Вы уже зарегистрированы.", reply_markup=get_main_menu_keyboard())
    elif isinstance(result, Exception):
        await message.answer("Произошла ошибка при регистрации. Попробуйте позже.")
    else:
        await message.answer("Регистрация завершена! Выберите действие:", reply_markup=get_main_menu_keyboard())

    await state.clear()

@dp.message(Command("unreg"))
async def unreg_handler(message: types.Message):
    """
    Обрабатывает команду /unreg для удаления данных пользователя.

    1) Удаляет пользователя из БД.
    2) Сообщает о завершении операции.
    """
    telegram_id = str(message.from_user.id)
    cursor = db.conn.cursor()
    cursor.execute('DELETE FROM t_client WHERE telegram_id = ?', (telegram_id,))
    db.conn.commit()
    cursor.close()

    await message.answer_sticker("CAACAgIAAxkBAAENXV1nZpOnX_PwZ4Xsmr1CSLBipbB6JQACml0AAp1FOEuRZgX-KGhUnjYE") # вы успешно отписались

@dp.message(Command("status"))
async def status_handler(message: types.Message):
    """
    Показывает текущие идентификаторы пользователя (Calendar ID, Todoist токен).

    Если не зарегистрирован, просим сделать /start.
    """
    telegram_id = str(message.from_user.id)

    calendar_id = db.get_calendar_id(telegram_id)
    todoist_token = db.get_todoist_token(telegram_id)

    if not calendar_id or not todoist_token:
        await message.answer("Вы ещё не зарегистрированы. Используйте команду /start для начала работы.")
        return
    status_message = (
        f"📋 **Ваш текущий статус:** 📋\n\n"
        f"🔹 **Google Calendar ID**: '{calendar_id}'\n"
        f"🔹 **Todoist API токен**: '{todoist_token}'\n\n"
        "Если вам нужно обновить данные:\n"
        "🔹 Используйте /update_calendar для Google Calendar.\n"
        "🔹 Используйте /update_todoist для Todoist API токен."
    )
    await message.answer(status_message, parse_mode="Markdown")

@dp.message(Command("update_calendar"))
async def update_calendar_handler(message: types.Message, state: FSMContext):
    """
    Начинает процесс обновления Google Calendar ID (команда /update_calendar).

    Проверяем, есть ли данные пользователя в БД. Если нет — /start, иначе ждём ввода нового ID.
    """
    telegram_id = str(message.from_user.id)
    if not is_user_registered(telegram_id):
        await message.answer("Сначала зарегистрируйтесь с помощью команды /start.")
        return

    await message.answer("Пожалуйста, отправьте ваш новый Google Calendar ID.")
    await state.set_state(UpdateStates.waiting_for_new_calendar_id)

@dp.message(UpdateStates.waiting_for_new_calendar_id)
async def process_new_calendar_id(message: types.Message, state: FSMContext):
    """
    Обрабатывает новый Google Calendar ID после /update_calendar.

    1) Проверяем валидность.
    2) Если валиден — обновляем в БД.
    """
    new_calendar_id = message.text.strip()
    telegram_id = str(message.from_user.id)

    if not calendar.validate_calendar_id(new_calendar_id):
        await message.answer_sticker("CAACAgIAAxkBAAENXVVnZpAk9PS1lNx4P-nqpTvDiFaDaQACt2IAA7QwSwxxEbxXoU5MNgQ") # неверный гугол календарь айди
        return

    result = db.update_calendar_id(telegram_id, new_calendar_id)
    if result:
        await message.answer("Ваш Google Calendar ID успешно обновлён!")
    else:
        await message.answer("Не удалось обновить Google Calendar ID. Попробуйте позже.")

    await state.clear()

@dp.message(Command("update_todoist"))
async def update_todoist_handler(message: types.Message, state: FSMContext):
    """
    Начинает процесс обновления Todoist API токена (команда /update_todoist).

    Если не зарегистрирован — /start, иначе ждём новый токен.
    """
    telegram_id = str(message.from_user.id)
    if not is_user_registered(telegram_id):
        await message.answer("Сначала зарегистрируйтесь с помощью команды /start.")
        return

    await message.answer("Пожалуйста, отправьте ваш новый Todoist API токен.")
    await state.set_state(UpdateStates.waiting_for_new_todoist_token)

@dp.message(UpdateStates.waiting_for_new_todoist_token)
async def process_new_todoist_token(message: types.Message, state: FSMContext):
    """
    Обрабатывает новый Todoist API токен после /update_todoist.

    1) Проверяем валидность токена (validate_token).
    2) Обновляем в БД.
    """
    new_todoist_token = message.text.strip()
    telegram_id = str(message.from_user.id)

    todoist_module = TodoistModule(new_todoist_token)
    if not todoist_module.validate_token():
        await message.answer_sticker("CAACAgIAAxkBAAENXVlnZpBVoCDz9AbxflDAeW1KWVXSCAACuWEAAq-EMUuLDDAtDmQyNzYE") # неверный тудуист токен
        return

    result = db.update_todoist_token(telegram_id, new_todoist_token)
    if result:
        await message.answer("Ваш Todoist API токен успешно обновлён!")
    else:
        await message.answer("Не удалось обновить Todoist API токен. Попробуйте позже.")

    await state.clear()

@dp.message(lambda message: message.text == "Добавить событие")
async def handle_add_event(message: types.Message, state: FSMContext):
    """
    Обработчик кнопки "Добавить событие".

    1) Сбрасывает текущее состояние.
    2) Устанавливает состояние ожидания информации о событии (waiting_for_event).
    """
    await state.clear()
    await message.answer("Пожалуйста, введите информацию о событии.")
    await state.set_state(UserStates.waiting_for_event)

@dp.message(lambda message: message.text == "Добавить задачу")
async def handle_add_task(message: types.Message, state: FSMContext):
    """
    Обработчик кнопки "Добавить задачу".

    1) Сбрасывает текущее состояние.
    2) Устанавливает состояние ожидания информации о задаче (waiting_for_task).
    """
    await state.clear()
    await message.answer("Пожалуйста, введите информацию о задаче.")
    await state.set_state(UserStates.waiting_for_task)


@dp.message()
async def handle_user_message(message: types.Message, state: FSMContext):
    """
    Обрабатывает прочие сообщения от пользователя после регистрации.

    Новая логика:
    1) Если сообщение не является текстом (стикер, gif, голосовое, фото и т.п.), отвечаем "мяу, красиво, но давай текстом".
    2) Иначе работаем с состояниями: waiting_for_event, waiting_for_task, или предлагаем меню.
    """
    try:
        telegram_id = str(message.from_user.id)

        # Проверка на тип сообщения:
        # Если не text (например, sticker, voice, фото, документ, gif и т.д.), просим текст
        if message.content_type != "text":
            # Отправка стикера вместо текста
            await message.answer_sticker("CAACAgIAAxkBAAENXUxnZo1mls407mn6UDUpVUF99h5WbwAChlwAAvosOEt4WHe1UgFjQTYE") # my honest reaction
            return

        if not is_user_registered(telegram_id):
            await message.answer("Пожалуйста, отправьте команду /start для начала работы.")
            return

        current_state = await state.get_state()
        user_input = message.text.strip()

        # Если пользователь ввёл всего 1 символ
        if len(user_input) <= 1:
            await message.answer_sticker("CAACAgIAAxkBAAENXVJnZo6pZBdtrSEzaS9uHzJ7cCeBKgAC1lUAAntVMEsGpxSQaHhx3DYE") # smol
            return

        # Логика обработки состояний:
        if current_state == UserStates.waiting_for_event.state:
            content = Query(
                client_id=telegram_id,
                current_time=datetime.now(),
                content=user_input
            )
            parsed_request = gpt_parser.parse_message(content)
            logger.info(f"Parsed request: {parsed_request}")

            if parsed_request and parsed_request.type == RequestType.EVENT:
                calendar_id = db.get_calendar_id(telegram_id)
                response = calendar.create_event(parsed_request, calendar_id)
                if response is None:
                    await message.answer(f"Событие '{parsed_request.body}' успешно добавлено в Google Calendar.")
                else:
                    await message.answer(f"Не удалось добавить событие в Google Calendar. Ошибка: {response}")

                await state.clear()
                await message.answer("Что хотите сделать дальше?", reply_markup=get_main_menu_keyboard())
            else:
                await message.answer("Не удалось распознать событие. Пожалуйста, введите информацию о событии ещё раз.")

        elif current_state == UserStates.waiting_for_task.state:
            content = Query(
                client_id=telegram_id,
                current_time=datetime.now(),
                content=user_input
            )
            parsed_request = gpt_parser.parse_message(content)
            logger.info(f"Parsed task: {parsed_request}")

            if parsed_request and parsed_request.type == RequestType.GOAL:
                todoist_token = db.get_todoist_token(telegram_id)
                todoist_module = TodoistModule(todoist_token)
                response = todoist_module.create_task(parsed_request)
                if response is None:
                    await message.answer(f"Задача '{parsed_request.body}' успешно добавлена в Todoist.")
                else:
                    await message.answer(f"Не удалось добавить задачу в Todoist. Ошибка: {response}")

                await state.clear()
                await message.answer("Что хотите сделать дальше?", reply_markup=get_main_menu_keyboard())
            else:
                await message.answer("Не удалось распознать задачу. Пожалуйста, введите информацию о задаче ещё раз.")

        else:
            # Если состояние не waiting_for_event и не waiting_for_task
            if user_input == "Добавить событие":
                await message.answer("Пожалуйста, введите информацию о событии.")
                await state.set_state(UserStates.waiting_for_event)
            elif user_input == "Добавить задачу":
                await message.answer("Пожалуйста, введите информацию о задаче.")
                await state.set_state(UserStates.waiting_for_task)
            else:
                content = Query(
                    client_id=telegram_id,
                    current_time=datetime.now(),
                    content=user_input
                )
                parsed_request = gpt_parser.parse_message(content)
                logger.info(f"Parsed task: {parsed_request}")

                if parsed_request and parsed_request.type == RequestType.GOAL:
                    todoist_token = db.get_todoist_token(telegram_id)
                    todoist_module = TodoistModule(todoist_token)
                    response = todoist_module.create_task(parsed_request)
                    if response is None:
                        await message.answer(f"Задача '{parsed_request.body}' успешно добавлена в Todoist.")
                    else:
                        await message.answer(f"Не удалось добавить задачу в Todoist. Ошибка: {response}")

                    await state.clear()
                    await message.answer("Что хотите сделать дальше?", reply_markup=get_main_menu_keyboard())
                elif parsed_request and parsed_request.type == RequestType.EVENT:
                    calendar_id = db.get_calendar_id(telegram_id)
                    response = calendar.create_event(parsed_request, calendar_id)
                    if response is None:
                        await message.answer(f"Событие '{parsed_request.body}' успешно добавлено в Google Calendar.")
                    else:
                        await message.answer(f"Не удалось добавить событие в Google Calendar. Ошибка: {response}")

                    await state.clear()
                    await message.answer("Что хотите сделать дальше?", reply_markup=get_main_menu_keyboard())
                
                await message.answer("Пожалуйста, выберите действие из меню.", reply_markup=get_main_menu_keyboard())

    except Exception as e:
        logger.exception(f"Произошла ошибка: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")

if __name__ == "__main__":
    print("Бот запущен")
    asyncio.run(dp.start_polling(bot))
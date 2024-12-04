from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from pathlib import Path

search_directory = Path('../')
for file_path in search_directory.rglob("Project"):
    project = file_path.resolve()

import sys
sys.path.append('project')

from Project.Todoist.Todoist_module import TodoistModule
from Project.Database import ClientsDB, Errors
from Project.Calendar.Calendar_module import CalendarModule
from Project.GPT.GPT_module import GPT
from Project.Query import Query
from Project.Request import RequestType

API_TOKEN = "8149845915:AAEoY53NSKqO5QntlTI6fwz4x-0j70e1X3o"

# Создаём объект бота и диспетчера
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()  # Хранилище состояний в памяти
dp = Dispatcher(storage=storage)

# Инициализация базы данных, Google Calendar и GPT парсера
db = ClientsDB()  # Подключаем базу данных
calendar = CalendarModule()  # Модуль для работы с Google Calendar
gpt_parser = GPT()  # Инициализация GPT парсера

# Определение состояний для регистрации и действий
class RegistrationStates(StatesGroup):
    waiting_for_google_calendar_id = State()
    waiting_for_todoist_token = State()

class UserStates(StatesGroup):
    waiting_for_event = State()
    waiting_for_task = State()

def get_main_menu_keyboard():
    """
    Создаёт клавиатуру с кнопками для главного меню.
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

@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    """
    Обрабатывает команду /start.
    """
    telegram_id = str(message.from_user.id)

    calendar_id_row = db.get_calendar_id(telegram_id)
    calendar_id = calendar_id_row[0] if calendar_id_row else None

    if calendar_id:
        # Если пользователь уже зарегистрирован
        await message.answer("Вы уже зарегистрированы.", reply_markup=get_main_menu_keyboard())
    else:
        # Начинаем процесс регистрации
        await message.answer(
            "Привет! Для начала работы нам нужны некоторые данные.\n"
            "Пожалуйста, отправьте ваш Google Calendar ID."
        )
        await state.set_state(RegistrationStates.waiting_for_google_calendar_id)

@dp.message(RegistrationStates.waiting_for_google_calendar_id)
async def process_google_calendar_id(message: types.Message, state: FSMContext):
    """
    Обрабатывает получение Google Calendar ID.
    """
    google_calendar_id = message.text.strip()
    telegram_id = str(message.from_user.id)

    # Сохраняем Google Calendar ID во временном состоянии
    await state.update_data(google_calendar_id=google_calendar_id)

    # Просим пользователя предоставить токен Todoist
    await message.answer(
        "Теперь, пожалуйста, отправьте ваш Todoist API токен.\n"
        "Вы можете найти его в настройках вашего Todoist аккаунта."
    )
    await state.set_state(RegistrationStates.waiting_for_todoist_token)

@dp.message(RegistrationStates.waiting_for_todoist_token)
async def process_todoist_token(message: types.Message, state: FSMContext):
    """
    Обрабатывает получение токена Todoist.
    """
    todoist_token = message.text.strip()
    telegram_id = str(message.from_user.id)

    # Получаем сохранённый Google Calendar ID
    data = await state.get_data()
    google_calendar_id = data.get('google_calendar_id')

    # Добавляем пользователя в базу данных
    result = db.add_client(telegram_id, google_calendar_id, todoist_token)
    if result == Errors.INTEGRITY_ERROR.value:  # Проверяем на уникальность
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
    """
    telegram_id = str(message.from_user.id)

    # Удаляем пользователя из базы данных
    cursor = db.conn.cursor()
    cursor.execute('DELETE FROM t_client WHERE telegram_id = ?', (telegram_id,))
    db.conn.commit()
    cursor.close()

    await message.answer("Вы успешно отписались. Для повторной регистрации используйте команду /start.")

@dp.message()
async def handle_user_message(message: types.Message, state: FSMContext):
    """
    Обрабатывает сообщения от пользователя после регистрации.
    """
    try:
        telegram_id = str(message.from_user.id)

        calendar_id = db.get_calendar_id(telegram_id)
        todoist_token = db.get_todoist_token(telegram_id)

        if not calendar_id or not todoist_token:
            # Пользователь не завершил регистрацию
            await message.answer("Пожалуйста, отправьте команду /start для начала работы.")
            return

        current_state = await state.get_state()

        if current_state == UserStates.waiting_for_event.state:
            # Обрабатываем ввод события
            content = Query(
                client_id=telegram_id,
                current_time=datetime.now(),
                content=message.text.strip()
            )
            parsed_request = gpt_parser.parse_message(content)
            logger.info(f"Parsed request: {parsed_request}")

            if parsed_request and parsed_request.type == RequestType.EVENT:
                response = calendar.create_event(parsed_request, calendar_id)
                if response is None:
                    await message.answer(f"Событие '{parsed_request.body}' успешно добавлено в Google Calendar.")
                else:
                    await message.answer(f"Не удалось добавить событие в Google Calendar. Ошибка: {response}")

                # Сбрасываем состояние и спрашиваем, что делать дальше
                await state.clear()
                await message.answer("Что хотите сделать дальше?", reply_markup=get_main_menu_keyboard())
            else:
                await message.answer("Не удалось распознать событие. Пожалуйста, введите информацию о событии ещё раз.")

        elif current_state == UserStates.waiting_for_task.state:
            # Обрабатываем ввод задачи
            content = Query(
                client_id=telegram_id,
                current_time=datetime.now(),
                content=message.text.strip()
            )
            parsed_request = gpt_parser.parse_message(content)
            logger.info(f"Parsed task: {parsed_request}")

            if parsed_request and parsed_request.type == RequestType.GOAL:
                todoist_module = TodoistModule(todoist_token)
                response = todoist_module.create_task(parsed_request)
                if response is None:
                    await message.answer(f"Задача '{parsed_request.body}' успешно добавлена в Todoist.")
                else:
                    await message.answer(f"Не удалось добавить задачу в Todoist. Ошибка: {response}")

                # Сбрасываем состояние и спрашиваем, что делать дальше
                await state.clear()
                await message.answer("Что хотите сделать дальше?", reply_markup=get_main_menu_keyboard())
            else:
                await message.answer("Не удалось распознать задачу. Пожалуйста, введите информацию о задаче ещё раз.")
        else:
            if message.text == "Добавить событие":
                await message.answer("Пожалуйста, введите информацию о событии.")
                await state.set_state(UserStates.waiting_for_event)
            elif message.text == "Добавить задачу":
                await message.answer("Пожалуйста, введите информацию о задаче.")
                await state.set_state(UserStates.waiting_for_task)
            else:
                await message.answer("Пожалуйста, выберите действие из меню.", reply_markup=get_main_menu_keyboard())
    except Exception as e:
        logger.exception(f"Произошла ошибка: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")


# Запуск бота
if __name__ == "__main__":
    print("ГООООООЙДАА!!")
    asyncio.run(dp.start_polling(bot))
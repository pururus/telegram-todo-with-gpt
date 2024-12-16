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

from Todoist.Todoist_module import TodoistModule
from Database.Database import ClientsDB, Errors
from Calendar.Calendar_module import CalendarModule
from GPT.GPT_module import GPT
from Query import Query
from Request import RequestType
from credentials import API_TOKEN

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

db = ClientsDB("client_DB")
calendar = CalendarModule()
gpt_parser = GPT()

class RegistrationStates(StatesGroup):
    waiting_for_google_calendar_id = State()
    waiting_for_todoist_token = State()

class UserStates(StatesGroup):
    waiting_for_event = State()
    waiting_for_task = State()

def get_main_menu_keyboard():
    """Создаёт клавиатуру с кнопками для главного меню."""
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
    """Обрабатывает команду /start."""
    telegram_id = str(message.from_user.id)
    calendar_id = db.get_calendar_id(telegram_id)

    if calendar_id:
        await message.answer("Вы уже зарегистрированы.", reply_markup=get_main_menu_keyboard())
    else:
        await message.answer(
            "Привет! Для начала работы отправьте ваш Google Calendar ID. "
            "Также предоставьте доступ для редактирования календаря: "
            "to-do-with-gpt-project@to-do-443214.iam.gserviceaccount.com"
        )
        await state.set_state(RegistrationStates.waiting_for_google_calendar_id)

@dp.message(RegistrationStates.waiting_for_google_calendar_id)
async def process_google_calendar_id(message: types.Message, state: FSMContext):
    """Обрабатывает получение Google Calendar ID."""
    google_calendar_id = message.text.strip()
    await state.update_data(google_calendar_id=google_calendar_id)
    await message.answer("Теперь отправьте ваш Todoist API токен.")
    await state.set_state(RegistrationStates.waiting_for_todoist_token)

@dp.message(RegistrationStates.waiting_for_todoist_token)
async def process_todoist_token(message: types.Message, state: FSMContext):
    """Обрабатывает получение токена Todoist."""
    todoist_token = message.text.strip()
    telegram_id = str(message.from_user.id)
    data = await state.get_data()
    google_calendar_id = data.get('google_calendar_id')

    result = db.add_client(telegram_id, google_calendar_id, todoist_token)
    if result == Errors.INTEGRITY_ERROR.value:
        await message.answer("Вы уже зарегистрированы.", reply_markup=get_main_menu_keyboard())
    elif isinstance(result, Exception):
        await message.answer("Произошла ошибка при регистрации. Попробуйте позже.")
    else:
        await message.answer("Регистрация завершена! Выберите действие:", reply_markup=get_main_menu_keyboard())

    await state.clear()

@dp.message(Command("update_calendar"))
async def update_calendar_handler(message: types.Message, state: FSMContext):
    """Обрабатывает команду /update_calendar для изменения Google Calendar ID."""
    telegram_id = str(message.from_user.id)
    if not db.get_calendar_id(telegram_id):
        await message.answer("Вы ещё не зарегистрированы. Используйте команду /start.")
        return
    await message.answer("Пожалуйста, отправьте новый Google Calendar ID:")
    await state.set_state(RegistrationStates.waiting_for_google_calendar_id)

@dp.message(RegistrationStates.waiting_for_google_calendar_id)
async def process_updated_google_calendar_id(message: types.Message, state: FSMContext):
    """Сохраняет новый Google Calendar ID в базу данных."""
    new_calendar_id = message.text.strip()
    telegram_id = str(message.from_user.id)
    if db.update_calendar_id(telegram_id, new_calendar_id):
        await message.answer("Google Calendar ID успешно обновлён!", reply_markup=get_main_menu_keyboard())
    else:
        await message.answer("Произошла ошибка. Попробуйте позже.")
    await state.clear()

@dp.message(Command("update_todoist"))
async def update_todoist_handler(message: types.Message, state: FSMContext):
    """Обрабатывает команду /update_todoist для изменения Todoist API токена."""
    telegram_id = str(message.from_user.id)
    if not db.get_todoist_token(telegram_id):
        await message.answer("Вы ещё не зарегистрированы. Используйте команду /start.")
        return
    await message.answer("Пожалуйста, отправьте новый Todoist API токен:")
    await state.set_state(RegistrationStates.waiting_for_todoist_token)

@dp.message(RegistrationStates.waiting_for_todoist_token)
async def process_updated_todoist_token(message: types.Message, state: FSMContext):
    """Сохраняет новый Todoist API токен в базу данных."""
    new_todoist_token = message.text.strip()
    telegram_id = str(message.from_user.id)
    if db.update_todoist_token(telegram_id, new_todoist_token):
        await message.answer("Todoist API токен успешно обновлён!", reply_markup=get_main_menu_keyboard())
    else:
        await message.answer("Произошла ошибка. Попробуйте позже.")
    await state.clear()

@dp.message()
async def handle_user_message(message: types.Message, state: FSMContext):
    """Обрабатывает сообщения пользователя."""
    telegram_id = str(message.from_user.id)
    calendar_id = db.get_calendar_id(telegram_id)
    todoist_token = db.get_todoist_token(telegram_id)

    if not calendar_id or not todoist_token:
        await message.answer("Вы не завершили регистрацию. Используйте команду /start.")
        return

    if message.text == "Добавить событие":
        await message.answer("Введите информацию о событии.")
        await state.set_state(UserStates.waiting_for_event)
    elif message.text == "Добавить задачу":
        await message.answer("Введите информацию о задаче.")
        await state.set_state(UserStates.waiting_for_task)
    else:
        await message.answer("Пожалуйста, выберите действие из меню.", reply_markup=get_main_menu_keyboard())

# Запуск бота
if __name__ == "__main__":
    print("Бот запущен!")
    asyncio.run(dp.start_polling(bot))

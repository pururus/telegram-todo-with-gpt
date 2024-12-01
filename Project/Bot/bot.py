from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram import F
import asyncio

# Токен, который ты получил от BotFather
API_TOKEN = "8149845915:AAEoY53NSKqO5QntlTI6fwz4x-0j70e1X3o"

# Создаем объект бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()  # Используем маршрутизатор для регистрации хэндлеров


# Обработчик команды /start
@router.message(Command("start"))
async def send_welcome(message: Message):
    await message.answer("здарова заебал че надо")


# Обработчик любого текста
@router.message(F.text)
async def echo_message(message: Message):
    user_text = message.text
    await message.answer(f"ты написал: {user_text}\nщас распарсим твою хуйню")


# Главная функция запуска бота
async def main():
    print("Бот запущен!")
    dp.include_router(router)  # Подключаем маршрутизатор
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


# Запускаем бота
if __name__ == "__main__":
    asyncio.run(main())

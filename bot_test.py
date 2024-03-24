import logging
from settings import bot_config
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


logging.basicConfig(level=logging.INFO)

bot = Bot(token=bot_config.bot_token)
dp = Dispatcher(bot)

# Создание стартового меню
start_menu_markup = ReplyKeyboardMarkup(resize_keyboard=True)
start_menu_markup.add(KeyboardButton("Отправить геолокацию"))

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.answer("Привет! Нажми кнопку ниже, чтобы поделиться своим местоположением.", reply_markup=start_menu_markup)

@dp.message_handler(lambda message: "отправить геолокацию" in message.text.lower())
async def request_location(message: types.Message):
    reply_markup = types.ReplyKeyboardRemove()  # Убираем клавиатуру
    await message.answer("Теперь отправьте свою геолокацию, нажав на кнопку внизу экрана.", reply_markup=reply_markup)
    await message.answer("Пожалуйста, поделись своим местоположением 🗺️", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(types.KeyboardButton("Отправить местоположение", request_location=True)))

@dp.message_handler(content_types=types.ContentType.LOCATION)
async def handle_location(message: types.Message):
    latitude = message.location.latitude
    longitude = message.location.longitude
    await message.answer(f"Ваши координаты: широта {latitude}, долгота {longitude}")

if __name__ == '__main__':
    import asyncio
    loop = asyncio.get_event_loop()
    loop.create_task(dp.start_polling())
    loop.run_forever()

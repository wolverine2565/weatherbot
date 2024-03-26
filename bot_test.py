import logging
import math

from aiogram.dispatcher import FSMContext

from database import orm
from settings import bot_config
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


logging.basicConfig(level=logging.INFO)

bot = Bot(token=bot_config.bot_token)
dp = Dispatcher(bot)

# Создание стартового меню
start_menu_markup = ReplyKeyboardMarkup(resize_keyboard=True)
start_menu_markup.add(KeyboardButton("Отправить геолокацию"))

# @dp.message_handler(commands=['start'])
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


# @dp.message_handler(regexp= 'История')
@dp.message_handler(commands=['start'])
async def get_reports(message: types.Message):
    current_page = 1
    reports = orm.get_reports(message.from_user.id)
    total_pages = math.ceil(len(reports) / 4)
    text = 'История запросов:'
    inline_markup = types.InlineKeyboardMarkup()
    for report in reports[:current_page*4]:
        inline_markup.add(types.InlineKeyboardButton(
            text=f'{report.city} {report.date.day}.{report.date.month}.{report.date.year}',
            callback_data=f'report_{report.id}'
        ))
    current_page += 1
    inline_markup.row(
        types.InlineKeyboardButton(text=f'{current_page-1}/{total_pages}', callback_data='None'),
        types.InlineKeyboardButton(text='Вперёд', callback_data=f'next_{current_page}')
    )
    await message.answer(text, reply_markup=inline_markup)

@dp.callback_query_handler(lambda call: 'users' not in call.data)
async def callback_query(call, state: FSMContext):
    query_type = call.data.split('_')[0]
    if query_type == 'delete' and call.data.split('_')[1] == 'report':
            report_id = int(call.data.split('_')[2])
            current_page = 1
            orm.delete_user_report(report_id)
            reports = orm.get_reports(call.from_user.id)
            total_pages = math.ceil(len(reports) / 4)
            inline_markup = types.InlineKeyboardMarkup()
            for report in reports[:current_page*4]:
                inline_markup.add(types.InlineKeyboardButton(
                    text=f'{report.city} {report.date.day}.{report.date.month}.{report.date.year}',
                    callback_data=f'report_{report.id}'
                ))
            current_page += 1
            inline_markup.row(
                types.InlineKeyboardButton(text=f'{current_page-1}/{total_pages}', callback_data='None'),
                types.InlineKeyboardButton(text='Вперёд', callback_data=f'next_{current_page}')
            )
            await call.message.edit_text(text='История запросов:', reply_markup=inline_markup)
            return
    async with state.proxy() as data:
        data['current_page'] = int(call.data.split('_')[1])
        await state.update_data(current_page=data['current_page'])
        if query_type == 'next':
            reports = orm.get_reports(call.from_user.id)
            total_pages = math.ceil(len(reports) / 4)
            inline_markup = types.InlineKeyboardMarkup()
            if data['current_page']*4 >= len(reports):
                for report in reports[data['current_page']*4-4:len(reports) + 1]:
                    inline_markup.add(types.InlineKeyboardButton(
                    text=f'{report.city} {report.date.day}.{report.date.month}.{report.date.year}',
                    callback_data=f'report_{report.id}'
                    ))
                data['current_page'] -= 1
                inline_markup.row(
                    types.InlineKeyboardButton(text='Назад', callback_data=f'prev_{data["current_page"]}'),
                    types.InlineKeyboardButton(text=f'{data["current_page"]+1}/{total_pages}', callback_data='None')
                )
                await call.message.edit_text(text="История запросов:", reply_markup=inline_markup)
                return
            for report in reports[data['current_page']*4-4:data['current_page']*4]:
                inline_markup.add(types.InlineKeyboardButton(
                text=f'{report.city} {report.date.day}.{report.date.month}.{report.date.year}',
                callback_data=f'report_{report.id}'
            ))
            data['current_page'] += 1
            inline_markup.row(
                types.InlineKeyboardButton(text='Назад', callback_data=f'prev_{data["current_page"]-2}'),
                types.InlineKeyboardButton(text=f'{data["current_page"]-1}/{total_pages}', callback_data='None'),
                types.InlineKeyboardButton(text='Вперёд', callback_data=f'next_{data["current_page"]}')
            )
            await call.message.edit_text(text="История запросов:", reply_markup=inline_markup)
        if query_type == 'prev':
            reports = orm.get_reports(call.from_user.id)
            total_pages = math.ceil(len(reports) / 4)
            inline_markup = types.InlineKeyboardMarkup()
            if data['current_page'] == 1:
                for report in reports[0:data['current_page']*4]:
                    inline_markup.add(types.InlineKeyboardButton(
                    text=f'{report.city} {report.date.day}.{report.date.month}.{report.date.year}',
                    callback_data=f'report_{report.id}'
                    ))
                data['current_page'] += 1
                inline_markup.row(
                    types.InlineKeyboardButton(text=f'{data["current_page"]-1}/{total_pages}', callback_data='None'),
                    types.InlineKeyboardButton(text='Вперёд', callback_data=f'next_{data["current_page"]}')
                )
                await call.message.edit_text(text="История запросов:", reply_markup=inline_markup)
                return
            for report in reports[data['current_page']*4-4:data['current_page']*4]:
                inline_markup.add(types.InlineKeyboardButton(
                text=f'{report.city} {report.date.day}.{report.date.month}.{report.date.year}',
                callback_data=f'report_{report.id}'
                ))
            data['current_page'] -= 1
            inline_markup.row(
                types.InlineKeyboardButton(text='Назад', callback_data=f'prev_{data["current_page"]}'),
                types.InlineKeyboardButton(text=f'{data["current_page"]+1}/{total_pages}', callback_data='None'),
                types.InlineKeyboardButton(text='Вперёд', callback_data=f'next_{data["current_page"]}'),
            )
            await call.message.edit_text(text="История запросов:", reply_markup=inline_markup)
        if query_type == 'report':
            reports = orm.get_reports(call.from_user.id)
            report_id = call.data.split('_')[1]
            inline_markup = types.InlineKeyboardMarkup()
            for report in reports:
                if report.id == int(report_id):
                    inline_markup.add(
                        types.InlineKeyboardButton(text='Назад', callback_data=f'reports_{data["current_page"]}'),
                        types.InlineKeyboardButton(text='Удалить зарос', callback_data=f'delete_report_{report_id}')
                    )
                    await call.message.edit_text(
                        text=f'Данные по запросу\n'
                        f'Город:{report.city}\n'
                        f'Температура:{report.temp}\n'
                        f'Ощущается как:{report.feels_like}\n'
                        f'Скорость ветра:{report.wind_speed}\n'
                        f'Давление:{report.pressure_mm}',
                        reply_markup=inline_markup
                    )
                    break
        if query_type == 'reports':
            reports = orm.get_reports(call.from_user.id)
            total_pages = math.ceil(len(reports) / 4)
            inline_markup = types.InlineKeyboardMarkup()
            data['current_page'] = 1
            for report in reports[:data['current_page']*4]:
                inline_markup.add(types.InlineKeyboardButton(
                    text=f'{report.city} {report.date.day}.{report.date.month}.{report.date.year}',
                    callback_data=f'report_{report.id}'
                ))
            data['current_page'] += 1
            inline_markup.row(
                types.InlineKeyboardButton(text=f'{data["current_page"]-1}/{total_pages}', callback_data='None'),
                types.InlineKeyboardButton(text='Вперёд', callback_data=f'next_{data["current_page"]}')
            )
            await call.message.edit_text(text='История запросов:', reply_markup=inline_markup)

@dp.message_handler(lambda message: message.from_user.id in bot_config.tg_bot_admin and message.text == 'Список пользователей')
async def get_all_users(message: types.Message):
    current_page = 1
    users = orm.get_all_users()
    total_pages = math.ceil(len(users) / 4)
    text = 'Все мои пользователи:'
    inline_markup = types.InlineKeyboardMarkup()
    for user in users[:current_page*4]:
        inline_markup.add(types.InlineKeyboardButton(
            text=f'{user.id}) \n'
                 f'id: {user.tg_id} \n'
                 f'Пользователь: {user.username} \n'
                 f'Полное имя: {user.full_name} \n'
                 f'Город: {user.city} \n'
                 f'Подключился: {user.connection_date.day}.{user.connection_date.month}.{user.connection_date.year} \n'
                 f'Отчётов: {len(user.reports)} ',
            callback_data=f'None'
        ))
    current_page += 1
    inline_markup.row(
        types.InlineKeyboardButton(text=f'{current_page-1}/{total_pages}', callback_data='None'),
        types.InlineKeyboardButton(text='Вперёд', callback_data=f'next_users_{current_page}')
    )
    await message.answer(text, reply_markup=inline_markup)







if __name__ == '__main__':
    import asyncio
    loop = asyncio.get_event_loop()
    loop.create_task(dp.start_polling())
    loop.run_forever()

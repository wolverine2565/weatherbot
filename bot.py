from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from settings import bot_config
from api_requests import request
from database import orm
import math


bot = Bot(token=bot_config.bot_token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class ChoiceCityWeather(StatesGroup):
    waiting_city = State()

class ChoiceCoordWeather(StatesGroup):
    waiting_coord = State()

class SetUserCity(StatesGroup):
    waiting_user_city = State()

class ChoiceSumm(StatesGroup):
    waiting_summ = State()

class DeleteParameter(StatesGroup):
    waiting_padameter_number = State()




class ChoiceParameter(StatesGroup):
    waiting_padameter_data = State()

@dp.message_handler(commands=['start'])
async def start_message(message: types.Message):
    orm.add_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    markup = await main_menu()
    text = f'Привет {message.from_user.first_name}, я бот, который расскжет тебе о погоде на сегодня'
    await message.answer(text, reply_markup=markup)

@dp.message_handler(regexp='Погода в моём городе')
async def get_user_city_weather(message: types.Message):
    markup = types.reply_keyboard.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('📋 Меню')
    markup.add(btn1)
    city = orm.get_user_city(message.from_user.id)
    if city is None:
        text = 'Пожалуйста установите город проживания'
        markup = types.reply_keyboard.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        btn1 = types.KeyboardButton('✈️ Установить свой город')
        markup.add(btn1)
        await message.answer(text, reply_markup=markup)
        return
    else:
        user_id = orm.get_user_id(message.from_user.id)
        if int(orm.get_current_balance(user_id)) < 1:
            await message.answer('Сначала пополните баланс в разделе "Настройки"')
            await state.reset_state()
            # выход без сохранения
        else:
            data = request.get_weather(city)
            orm.create_report(message.from_user.id, data["temp"], data["feels_like"], data["wind_speed"], data["pressure_mm"], city)
            orm.bill_use(user_id)
            text = f'Погода в {city}\nТемпература: {data["temp"]} C\nОщущается как: {data["feels_like"]} C \nСкорость ветра: {data["wind_speed"]}м/с\nДавление: {data["pressure_mm"]}мм'
            await message.answer(text, reply_markup=markup)
    """переработать данный хендлер чтобы сразу запрашивался город нахождения"""

@dp.message_handler(regexp='Погода в другом месте')
async def city_start(message: types.Message):
    markup = types.reply_keyboard.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('📋 Меню')
    markup.add(btn1)
    text = 'Введите название города'
    await message.answer(text, reply_markup=markup)
    await ChoiceCityWeather.waiting_city.set()

# Добалена погода по геолокации
@dp.message_handler(lambda message: "Отправить геолокацию" in message.text)
async def request_location(message: types.Message):
    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    reply_markup.add(types.KeyboardButton("Отправить местоположение 🗺", request_location=True))
    reply_markup.add(types.KeyboardButton("📋 Меню"))
    await message.answer("Пожалуйста, поделись своим местоположением 🗺", reply_markup=reply_markup)

@dp.message_handler(content_types=types.ContentType.LOCATION)
async def handle_location(message: types.Message):
    user_id = orm.get_user_id(message.from_user.id)
    if int(orm.get_current_balance(user_id)) < 1:
        await message.answer('Сначала пополните баланс в разделе "Настройки"')
        await state.reset_state()
        # выход без сохранения
    else:
        latitude = message.location.latitude
        longitude = message.location.longitude
        data = request.get_weather_coord(latitude, longitude)
        markup = await main_menu()
        orm.create_report(message.from_user.id, data['fact']['temp'], data['fact']['feels_like'], data['fact']['wind_speed'], data['fact']['pressure_mm'],
                      data['geo_object']['locality']['name'])
        orm.bill_use(user_id)
        text = f'Погода в {data["geo_object"]["locality"]["name"]}\nТемпература: {data["fact"]["temp"]} C\nОщущается как: {data["fact"]["feels_like"]} C \nСкорость ветра: {data["fact"]["wind_speed"]}м/с\nДавление: {data["fact"]["pressure_mm"]}мм'
        await message.answer(text, reply_markup=markup)


@dp.message_handler(state=ChoiceCityWeather.waiting_city)
async def city_chosen(message: types.Message, state: FSMContext):
    user_id = orm.get_user_id(message.from_user.id)
    if int(orm.get_current_balance(user_id)) < 1:
        await message.answer('Сначала пополните баланс в разделе "Настройки"')
        await state.reset_state()
        #выход без сохранения
    elif message.text[0].islower():
        await message.answer('Названия городов пишутся с большой буквы)')
        return
    elif message.text == 'Меню' or message.text == '📋 Меню':
        await start_message(message)
        await state.reset_state()
        #выход без сохранения
    else:
        await state.update_data(waiting_city=message.text)
        markup = await main_menu()
        user_id = orm.get_user_id(message.from_user.id)
        city = await state.get_data()
        data = request.get_weather(city.get('waiting_city'))
        orm.create_report(message.from_user.id, data["temp"], data["feels_like"], data["wind_speed"], data["pressure_mm"],
                      city.get('waiting_city'))
        orm.bill_use(user_id)
        orm.new_city_add(city.get('waiting_city')) # запись нового города в таблицу city
        text = f'Погода в {city.get("waiting_city")}\nТемпература: {data["temp"]} C\nОщущается как: {data["feels_like"]} C \nСкорость ветра: {data["wind_speed"]}м/с\nДавление: {data["pressure_mm"]}мм'
        await message.answer(text, reply_markup=markup)
        await state.finish()


@dp.message_handler(regexp='Меню')
async def start_message(message: types.Message):
    markup = await main_menu()
    text = f'Привет {message.from_user.first_name}, я бот, который расскжет тебе о погоде на сегодня'
    await message.answer(text, reply_markup=markup)

@dp.message_handler(regexp='Установить свой город')
async def set_user_city_start(message: types.Message):
    markup = types.reply_keyboard.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('Меню')
    markup.add(btn1)
    text = 'В каком городе проживаете?'
    await message.answer(text, reply_markup=markup)
    await SetUserCity.waiting_user_city.set()

@dp.message_handler(state=SetUserCity.waiting_user_city)
async def user_city_chosen(message: types.Message, state: FSMContext):
    if message.text[0].islower():
        await message.answer('Названия городов пишутся с большой буквы)')
        return
    elif message.text == 'Меню' or message.text == '📋 Меню':
        await start_message(message)
        await state.reset_state()
        #выход без сохранения
    else:
        await state.update_data(waiting_user_city=message.text)
        user_data = await state.get_data()
        orm.set_user_city(message.from_user.id, user_data.get('waiting_user_city'))
        markup = await main_menu()
        text = f'Запомнил, {user_data.get("waiting_user_city")} ваш город'
        await message.answer(text, reply_markup=markup)
        await state.finish()


@dp.message_handler(regexp= 'История')
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

@dp.message_handler(lambda message: (message.text == 'Администратор' or message.text == '⚙️ Админ-панель'))
async def admin_panel(message: types.Message):
    if message.from_user.id in bot_config.tg_bot_admin or orm.check_value('tg_bot_admin', f'{message.from_user.id}') == True or orm.check_value('tg_bot_admin', f'{message.from_user.username}') == True:
        markup = types.reply_keyboard.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('📑 Список пользователей')
        btn2 = types.KeyboardButton('🗓 Версия программы')
        btn3 = types.KeyboardButton('📋 Меню')
        btn4 = types.KeyboardButton('⚙️ Системные параметры️')
        markup.add(btn1, btn2, btn3, btn4)
        text = f'Админ-панель'
        await message.answer(text, reply_markup=markup)
    else:
        markup = types.reply_keyboard.ReplyKeyboardMarkup(resize_keyboard=True)
        text = f'Вы не являетесь администратором'
        btn1 = types.KeyboardButton('Меню')
        await message.answer(text, reply_markup=markup)

# @dp.message_handler(lambda message: message.from_user.id in bot_config.tg_bot_admin and message.text == '📑 Список пользователей')
@dp.message_handler(lambda message: (message.from_user.id in bot_config.tg_bot_admin or orm.check_value('tg_bot_admin', f'{message.from_user.id}') == True or orm.check_value('tg_bot_admin', f'{message.from_user.username}') == True) and message.text == '📑 Список пользователей')
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

@dp.callback_query_handler(lambda call: 'users' in call.data)
async def callback_query(call, state: FSMContext):
    query_type = call.data.split('_')[0]
    async with state.proxy() as data:
        data['current_page'] = int(call.data.split('_')[2])
        await state.update_data(current_page=data['current_page'])
        if query_type == 'next':
            users = orm.get_all_users()
            total_pages = math.ceil(len(users) / 4)
            inline_markup = types.InlineKeyboardMarkup()
            if data['current_page']*4 >= len(users):
                for user in users[data['current_page']*4-4:len(users) + 1]:
                    inline_markup.add(types.InlineKeyboardButton(
                    text=f'{user.id}) id: {user.tg_id} Подключился: {user.connection_date.day}.{user.connection_date.month}.{user.connection_date.year} Отчётов: {len(user.reports)}',
                    callback_data=f'None'
                    ))
                data['current_page'] -= 1
                inline_markup.row(
                    types.InlineKeyboardButton(text='Назад', callback_data=f'prev_users_{data["current_page"]}'),
                    types.InlineKeyboardButton(text=f'{data["current_page"]+1}/{total_pages}', callback_data='None')
                )
                await call.message.edit_text(text='Все мои пользователи:', reply_markup=inline_markup)
                return
            for user in users[data['current_page']*4-4:data['current_page']*4]:
                inline_markup.add(types.InlineKeyboardButton(
                text=f'{user.id}) id: {user.tg_id} Подключился: {user.connection_date.day}.{user.connection_date.month}.{user.connection_date.year} Отчётов: {len(user.reports)}',
                callback_data=f'None'
            ))
            data['current_page'] += 1
            inline_markup.row(
                types.InlineKeyboardButton(text='Назад', callback_data=f'prev_users_{data["current_page"]-2}'),
                types.InlineKeyboardButton(text=f'{data["current_page"]-1}/{total_pages}', callback_data='None'),
                types.InlineKeyboardButton(text='Вперёд', callback_data=f'next_users_{data["current_page"]}')
            )
            await call.message.edit_text(text='Все мои пользователи:', reply_markup=inline_markup)
        if query_type == 'prev':
            users = orm.get_all_users()
            total_pages = math.ceil(len(users) / 4)
            inline_markup = types.InlineKeyboardMarkup()
            if data['current_page'] == 1:
                for user in users[0:data['current_page']*4]:
                    inline_markup.add(types.InlineKeyboardButton(
                    text=f'{user.id}) id: {user.tg_id} Подключился: {user.connection_date.day}.{user.connection_date.month}.{user.connection_date.year} Отчётов: {len(user.reports)}',
                    callback_data=f'None'
                    ))
                data['current_page'] += 1
                inline_markup.row(
                    types.InlineKeyboardButton(text=f'{data["current_page"]-1}/{total_pages}', callback_data='None'),
                    types.InlineKeyboardButton(text='Вперёд', callback_data=f'next_users_{data["current_page"]}')
                )
                await call.message.edit_text(text='Все мои пользователи:', reply_markup=inline_markup)
                return
            for user in users[data['current_page']*4-4:data['current_page']*4]:
                inline_markup.add(types.InlineKeyboardButton(
                text=f'{user.id}) id: {user.tg_id} Подключился: {user.connection_date.day}.{user.connection_date.month}.{user.connection_date.year} Отчётов: {len(user.reports)}',
                callback_data=f'None'
                ))
            data['current_page'] -= 1
            inline_markup.row(
                types.InlineKeyboardButton(text='Назад', callback_data=f'prev_users_{data["current_page"]}'),
                types.InlineKeyboardButton(text=f'{data["current_page"]+1}/{total_pages}', callback_data='None'),
                types.InlineKeyboardButton(text='Вперёд', callback_data=f'next_users_{data["current_page"]}'),
            )
            await call.message.edit_text(text='Все мои пользователи:', reply_markup=inline_markup)

@dp.message_handler(lambda message: message.from_user.id in bot_config.tg_bot_admin and message.text == '🗓 Версия программы')
async def get_version(message: types.Message):
    markup = types.reply_keyboard.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('📋 Меню')
    btn2 = types.KeyboardButton('⚙️ Админ-панель')
    markup.add(btn1, btn2)
    text =  f'Версия 1,25:' \
            f'\n- Добавлена возможность назначать администраторов в разделе "Настройки"' \
            f'\n- Добавлена возможнось самостоятельно добавлять API-ключи' \
            f'\nВерсия 1.24:' \
            f'\n - Добавлена возможность пополнения баланса в настройках' \
            f'\nВерсия 1.23:' \
            f'\n - Добавлены иконки в меню' \
            f'\nВерсия 1.22:' \
            f'\n -Добавлен раздел "Статистика"' \
            f'\nВерсия 1.21: ' \
            f'\n- Исправлены ошибки ' \
            f'\n- Добавлена погода по геолокации' \
            f'\n- Доработана панель администратора' \
            f'\n- Исправлена ошибка при которой название кнопки "Меню" сохранялось как новый город'
    await message.answer(text, reply_markup=markup)

@dp.message_handler(lambda message: message.text == 'Настройки' or message.text == '🛠 Настройки')
async def settings(message: types.Message):
    markup = types.reply_keyboard.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('⚙️ Админ-панель')
    btn2 = types.KeyboardButton('🗓 Версия программы')
    btn3 = types.KeyboardButton('📋 Меню')
    btn4 = types.KeyboardButton('📈 Статистика')
    btn5 = types.KeyboardButton('🧮 Баланс')
    text =  'Настройки'
    markup.add(btn1, btn2, btn3, btn4, btn5)
    await message.answer(text, reply_markup=markup)

@dp.message_handler(lambda message: message.text == 'Статистика' or message.text == '📈 Статистика')
async def settings(message: types.Message):
    markup = types.reply_keyboard.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    max_report = orm.get_max_report()
    text = f'Количество запросов: {max_report}' \
           f'\nСамый популярный город в запросах: {orm.get_popular_city()}'
    btn1 = types.KeyboardButton('Меню')
    markup.add(btn1)
    await message.answer(text, reply_markup=markup)

@dp.message_handler(regexp='Пополнить баланс')
async def city_start(message: types.Message):
    markup = types.reply_keyboard.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('📋 Меню')
    markup.add(btn1)
    text = 'Введите сумму для пополнения'
    await message.answer(text, reply_markup=markup)
    await ChoiceSumm.waiting_summ.set()

@dp.message_handler(state=ChoiceSumm.waiting_summ)
async def balance_up(message: types.Message, state: FSMContext):
    if message.text.isdigit():
        if int(message.text) > 10:
            await message.answer(f'Сумма пополнения не должна быть больше 10')
        elif int(message.text) <= 0:
            await message.answer(f'Сумма пополнения должна быть больше нуля')
        else:
            user_id = orm.get_user_id(message.from_user.id)
            orm.bill_charge(user_id, message.text)
            await message.answer(f'Ваш баланс пополнен на {message.text} запросов'
                                f'\nТекущий баланс: {orm.get_current_balance(user_id)}')
        return
    elif message.text == 'Меню' or message.text == '📋 Меню':
        await start_message(message)
        await state.reset_state()
        #выход без сохранения
    else:
        await message.answer(f'Введите сумму числом')

@dp.message_handler(regexp='Баланс')
async def city_start(message: types.Message):
    markup = types.reply_keyboard.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('📋 Меню')
    btn2 = types.KeyboardButton('💰 Пополнить баланс')
    user_id = orm.get_user_id(message.from_user.id)
    balance = orm.get_current_balance(user_id)
    markup.add(btn1, btn2)
    text = f'Ваш баланс {balance} запросов'
    await message.answer(text, reply_markup=markup)
    await ChoiceSumm.waiting_summ.set()

@dp.message_handler(regexp='Системные параметры')
async def city_start(message: types.Message):
    markup = types.reply_keyboard.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('📋 Меню')
    btn2 = types.KeyboardButton('🔧 Добавить новый параметр')
    btn3 = types.KeyboardButton('❌ Удалить параметр')
    markup.add(btn1, btn2, btn3)
    text = 'Системные параметры\n'
    all_configs = orm.get_all_configs()
    for config in all_configs[:50]:  # Ограничиваем вывод первыми 50 записями
        text += (
            f"Номер: {config.id}\n"
            f"Дата: {config.date.day}.{config.date.month}.{config.date.year}\n"
            f"Добавлен пользователем: {orm.get_username(config.createby)}\n"
            f"Название: {config.name}\n"
            f"Значение: {config.value}\n\n"
        )
    await message.answer(text, reply_markup=markup)

@dp.message_handler(regexp='Добавить новый параметр')
async def add_parameter(message: types.Message, state: FSMContext):
    await message.answer("Введите название и значение параметра через запятую и пробел\n"
                         "(Например: название_параметра, значение параметра)")
    await ChoiceParameter.waiting_padameter_data.set()


@dp.message_handler(state=ChoiceParameter.waiting_padameter_data)
async def parameter_chosen(message: types.Message, state: FSMContext):
    if message.text == 'Меню' or message.text == '📋 Меню':
        await start_message(message)
        await state.reset_state()
        #выход без сохранения
    else:
        userid = orm.get_user_id(message.from_user.id)
        data = message.text.split(', ')
        markup = await main_menu()
        p_name = data[0]
        p_value = data [1]
        orm.add_config(userid, p_name, p_value)
        text = f'Параметр {data[0]} успешно добавлен'
        await message.answer(text, reply_markup=markup)
        await state.finish()

@dp.message_handler(regexp='Удалить параметр')
async def del_parameter(message: types.Message, state: FSMContext):
    await message.answer("Введите номер параметра:")
    await DeleteParameter.waiting_padameter_number.set()

@dp.message_handler(state=DeleteParameter.waiting_padameter_number)
async def parameter_del_chosen(message: types.Message, state: FSMContext):
    markup = await main_menu()
    if message.text == 'Меню' or message.text == '📋 Меню':
        await start_message(message)
        await state.reset_state()
        #выход без сохранения
    else:
        if message.text.isdigit():
            if orm.check_parameter_number(message.text) == True:
                orm.del_config(message.text)
                await message.answer(f'Параметр номер {message.text} удален')
                await state.reset_state()
            else: await message.answer(f'Параметр c номером {message.text} не найден')
        else:
            await message.answer(f'Введите число')
            await state.reset_state()

async def main_menu():
    markup = types.reply_keyboard.ReplyKeyboardMarkup(row_width=2)
    btn1 = types.KeyboardButton('🏠 Погода в моём городе')
    btn2 = types.KeyboardButton('🌎 Погода в другом месте')
    btn3 = types.KeyboardButton('📜 История')
    btn4 = types.KeyboardButton('✈️ Установить свой город')
    btn5 = types.KeyboardButton('🗺 Отправить геолокацию')
    btn6 = types.KeyboardButton('🛠 Настройки')
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    return markup

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

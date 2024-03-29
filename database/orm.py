from sqlalchemy import create_engine, func
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import sessionmaker
from .models import Base, User, WeatherReport, City, Billing

from settings import database_config

engine = create_engine(database_config.url, echo=True)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# регистрация по кнопке /start
def add_user(tg_id, username, full_name):
    session = Session()
    user = session.query(User).filter(User.tg_id == tg_id).first()
    if user is None:
        new_user = User(tg_id=tg_id, username=username, full_name=full_name)
        session.add(new_user)
        session.commit()

# установить город проживания
def set_user_city(tg_id, city_name):
    session = Session()
    city = session.query(City).filter(City.city_name == city_name).first()
    if city is None:
        city = City(city_name=city_name)
        session.add(city)
        session.commit()
    user = session.query(User).filter(User.tg_id == tg_id).first()
    if user:
        user.city = city
        session.commit()
        print(f"City updated for user with tg_id: {tg_id}")
    else:
        print(f"User with tg_id: {tg_id} not found.")
    session.close()

# создание прогноза
def create_report(tg_id, temp, feels_like, wind_speed, pressure_mm, city):
    session = Session()
    user = session.query(User).filter(User.tg_id == tg_id).first()
    try:
        existing_city = session.query(City).filter(City.city_name == city).one()
    except NoResultFound:
        new_city = City(city_name=city)
        session.add(new_city)
        session.flush()
        session.refresh(new_city)
    else:
        new_city = existing_city # Добавлена проверка существующей записи в таблице city
    new_report = WeatherReport(temp=temp, feels_like=feels_like, wind_speed=wind_speed, pressure_mm=pressure_mm, city_id=new_city.id, owner=user.id)
    session.add(new_report)
    session.commit()

# город проживания
def get_user_city(tg_id):
    session = Session()
#     user = session.query(User).filter(User.tg_id == tg_id).first()
#     return user.city
    user = session.query(User).filter(User.tg_id == tg_id).first()
    if user:
        city = user.city.city_name if user.city else None
        session.close()
        return city
    else:
        print(f"User with tg_id: {tg_id} not found.")
        session.close()
        return None


# получить историю
def get_reports(tg_id):
    session = Session()
    user = session.query(User).filter(User.tg_id == tg_id).first()
    reports = user.reports
    return reports

# удаление запроса
def delete_user_report(report_id):
    session = Session()
    report = session.get(WeatherReport, report_id)
    session.delete(report)
    session.commit()

# список зарегистрированных пользователей
def get_all_users():
    session = Session()
    users = session.query(User).all()
    return users
# количество запросов по максимальному id
def get_max_report():
    session = Session()
    max_id = session.query(func.max(WeatherReport.id)).scalar()
    return max_id
# самый популярный город в запросах
def get_popular_city():
    session = Session()
    # subquery = session.query(WeatherReport.city, func.count(WeatherReport.city).label('city_count')) \
    #     .group_by(WeatherReport.city) \
    #     .order_by(func.count(WeatherReport.city).desc()) \
    #     .limit(1).subquery()
    # result = session.query(subquery.c.city).first()
    # city_with_max_reports = result[0] if result is not None else None
    # return city_with_max_reports
    subquery = session.query(func.count(WeatherReport.city_id).label('report_count'),
                             WeatherReport.city_id). \
        group_by(WeatherReport.city_id). \
        order_by(func.count(WeatherReport.city_id).desc()). \
        limit(1).subquery('t')
    result = session.query(City.city_name). \
        join(subquery, City.id == subquery.c.city_id).first()
    if result:
        city_name = result[0]
        return city_name
    else:
        return
        session.close()

# Добавление нового города в таблицу city
def new_city_add(city):
    session = Session()
    # Проверка наличия города в таблице
    existing_city = session.query(City).filter_by(city_name=city).first()
    if existing_city is None:
        # Город отсутствует в таблице, добавляем его
        new_city = City(city_name=city)
        session.add(new_city)
        session.commit()

# Пополнение счета
def bill_charge(user_id, balance):
    session = Session()
    try:
        new_transaction = Billing(user_id=user_id, date=func.current_timestamp(), balance=balance)
        session.add(new_transaction)
        session.commit()
        return f"Баланс пополнен на {balance} единиц"
    except Exception as e:
        session.rollback()
        return "Ошибка пополнения баланса"
    finally:
        session.close()
# Списание со счета
def bill_use(u_id):
    session = Session()
    try:
        current_balance = session.query(func.sum(Billing.balance)).filter(Billing.user_id == u_id).scalar() or 0

        if current_balance > 0:
            new_transaction = Billing(user_id=u_id, date=func.current_timestamp(), balance=-1)
            session.add(new_transaction)
            session.commit()
    except Exception as e:
        session.rollback()
    finally:
        session.close()
# Запрос баланса
def get_current_balance(u_id):
    session = Session()
    try:
        current_balance = session.query(func.sum(Billing.balance)).filter(Billing.user_id == u_id).scalar() or 0
        return current_balance
    except Exception as e:
        return 0
    finally:
        session.close()

def get_user_id(telegram_id):
    session = Session()
    try:
        user_id = session.query(User.id).filter(User.tg_id == telegram_id).scalar()
        return user_id if user_id else 0
    except Exception as e:
        return 0
    finally:
        session.close()



from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from .models import Base, User, WeatherReport

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
def set_user_city(tg_id, city):
    session = Session()
    user = session.query(User).filter(User.tg_id == tg_id).first()
    user.city = city
    session.commit()

# создание прогноза
def create_report(tg_id, temp, feels_like, wind_speed, pressure_mm, city):
    session = Session()
    user = session.query(User).filter(User.tg_id == tg_id).first()
    new_report = WeatherReport(temp=temp, feels_like=feels_like, wind_speed=wind_speed, pressure_mm=pressure_mm, city=city, owner=user.id)
    session.add(new_report)
    session.commit()

# город проживания
def get_user_city(tg_id):
    session = Session()
    user = session.query(User).filter(User.tg_id == tg_id).first()
    return user.city

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
    subquery = session.query(WeatherReport.city, func.count(WeatherReports.city).label('city_count')) \
        .group_by(WeatherReport.city) \
        .order_by(func.count(WeatherReport.city).desc()) \
        .limit(1).subquery()
    result = session.query(subquery.c.city).first()
    city_with_max_reports = result[0] if result is not None else None
    return city_with_max_reports
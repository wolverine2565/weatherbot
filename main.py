import json
import requests

from database.models import User, WeatherReport, City
from database.orm import Session
from settings import api_config



def get_city_coord(city):
    payload = {'geocode': city, 'apikey': api_config.geo_key, 'format': 'json'}
    r = requests.get('https://geocode-maps.yandex.ru/1.x', params=payload)
    geo = json.loads(r.text)
    return geo['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos'];



def get_weather(city):
    coordinates = get_city_coord(city).split()
    payload = {'lat': coordinates[1], 'lon': coordinates[0], 'lang': 'ru_RU'}
    r = requests.get('https://api.weather.yandex.ru/v2/forecast', params=payload, headers=api_config.weather_key)
    weather_data = json.loads(r.text)
    # return weather_data['fact']
    return weather_data;

# print(get_weather('Калининград'))

# print(get_city_coord('Калининград'))


def get_weather_coord(coordinates):
    coordinates = coordinates.split()
    payload = {'lat': coordinates[1], 'lon': coordinates[0], 'lang': 'ru_RU'}
    r = requests.get('https://api.weather.yandex.ru/v2/forecast', params=payload, headers=api_config.weather_key)
    weather_data = json.loads(r.text)
    district = weather_data['geo_object']['district']['name']
    locality = weather_data['geo_object']['locality']['name']
    country = weather_data['geo_object']['country']['name']
    temp = weather_data['fact']['temp']
    feels_like = weather_data['fact']['feels_like']
    wind_speed = weather_data['fact']['wind_speed']
    pressure_mm = weather_data['fact']['pressure_mm']
    return f'Погода в {district}, город: {locality}, {country}: ' \
           f' температура воздуха: {temp} C' \
           f' ощущается как: {feels_like} C' \
           f' скорость ветра: {wind_speed} м/с' \
           f' амтосферное давление {pressure_mm} мм.рт.ст';

# print(get_weather_coord('30.314997 59.938784'))

def add_user(tg_id, username, full_name):
    session = Session()
    user = session.query(User).filter(User.tg_id == tg_id).first()
    if user is None:
        new_user = User(tg_id=tg_id, username=username, full_name=full_name)
        session.add(new_user)
        session.commit()

from sqlalchemy import func

# Assuming you have the required imports and SQLAlchemy models already set up
def get_popular_city():
# Create a session
    session = Session()
# Subquery to get the city_id with the highest number of weather reports
    subquery = session.query(func.count(WeatherReport.city_id).label('report_count'),
                         WeatherReport.city_id).\
        group_by(WeatherReport.city_id).\
        order_by(func.count(WeatherReport.city_id).desc()).\
        limit(1).subquery('t')

# Main query to get the city name for the city with the highest number of weather reports
    result = session.query(City.city_name).\
    join(subquery, City.id == subquery.c.city_id).first()
    if result:
        city_name = result[0]
        return city_name
    else:
        return

# Close the session
        session.close()

get_popular_city()


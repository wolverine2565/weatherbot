import json

import requests

from settings import api_config

def get_city_coord(city):
    payload = {'geocode' : city, 'apikey' : api_config.geo_key, 'format' : 'json'}
    r = requests.get('https://geocode-maps.yandex.ru/1.x', params=payload)
    geo = json.loads(r.text)
    return geo['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos']

def get_weather(city):
    coordinates = get_city_coord(city).split()
    payload = {'lat' : coordinates[1], 'lon' : coordinates[0], 'lang' : 'ru_RU'}
    r = requests.get('https://api.weather.yandex.ru/v2/forecast', params=payload, headers=api_config.weather_key)
    weather_data = json.loads(r.text)
    return weather_data['fact']

def get_weather_coord(lat, lon):
    # coordinates = coordinates.split()
    payload = {'lat': lat, 'lon': lon, 'lang': 'ru_RU'}
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
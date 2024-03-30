from database import orm

weather_key = {'X-Yandex-API-Key': orm.select_config_value_by_name('weather_key')}

geo_key = orm.select_config_value_by_name('geo_key')



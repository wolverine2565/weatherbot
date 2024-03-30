from datetime import datetime

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'Users'
    id = Column(Integer, primary_key=True)
    connection_date = Column(DateTime, default=datetime.now, nullable=False)
    tg_id = Column(BigInteger, nullable=False)
    city_id = Column(Integer, ForeignKey('City.id'), nullable=True)
    username = Column(String)
    full_name = Column(String)
    reports = relationship('WeatherReport', backref='report', lazy=True, cascade='all, delete-orphan')
    city = relationship("City")

    def __repr__(self):
        return self.tg_id


class WeatherReport(Base):
    __tablename__ = 'WeatherReports'
    id = Column(Integer, primary_key=True)
    owner = Column(Integer, ForeignKey('Users.id'), nullable=False)
    date = Column(DateTime, default=datetime.now, nullable=False)
    temp = Column(Integer, nullable=False)
    feels_like = Column(Integer, nullable=False)
    wind_speed = Column(Integer, nullable=False)
    pressure_mm = Column(Integer, nullable=False)
    city_id = Column(Integer, ForeignKey('City.id'), nullable=False)
    city = relationship("City")

    def __repr__(self):
        return self.city


class City(Base):
    __tablename__ = 'City'
    id = Column(Integer, primary_key=True)
    city_name = Column(String, nullable=False)

    def __repr__(self):
        return self.city_name


class Billing(Base):
    __tablename__ = 'Billing'
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=datetime.now, nullable=False)
    user_id = Column(Integer, ForeignKey('Users.id'), nullable=False)
    balance = Column(Integer, nullable=False)

    def __repr__(self):
        return self.balance

class Config(Base):
    __tablename__ = 'Config'
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=datetime.now, nullable=False)
    createby = Column(Integer, ForeignKey('Users.id'), nullable=False)
    name = Column(String, nullable=False)
    value = Column(String, nullable=False)

    def __repr__(self):
        return self.all
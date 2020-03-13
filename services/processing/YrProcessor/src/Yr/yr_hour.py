# TODO: change the name of this file
from sqlalchemy import BigInteger, Column, String, Float, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class WeatherHour(Base):
    __tablename__ = 'weather'
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(BigInteger)
    location = Column(String(100))
    location_name = Column(String(100))
    time_from = Column(BigInteger)
    time_to = Column(BigInteger)
    precipitation = Column(Float)
    wind_speed = Column(Float)
    temperature = Column(Float)
    air_pressure = Column(Float)

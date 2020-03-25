from sqlalchemy import Column, String, Float, Integer, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class WeatherHour(Base):
    __tablename__ = 'yr_weather'
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(TIMESTAMP)
    location = Column(String(100))
    location_name = Column(String(100))
    time_from = Column(TIMESTAMP)
    time_to = Column(TIMESTAMP)
    precipitation = Column(Float)
    wind_speed = Column(Float)
    temperature = Column(Float)
    air_pressure = Column(Float)

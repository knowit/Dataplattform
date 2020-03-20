from sqlalchemy import Column, String, Float, Integer, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()


class UBWFagtimer(Base):
    __tablename__ = 'ubw_fagtimer'
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(TIMESTAMP)
    reg_period = Column(String, unique=True)
    used_hours = Column(Float(asdecimal=True))

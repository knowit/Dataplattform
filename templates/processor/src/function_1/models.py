from sqlalchemy import Column, Integer, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()


class Schema(Base):
    __tablename__ = 'example_table'
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(TIMESTAMP)

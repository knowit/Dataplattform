from sqlalchemy import create_engine, Column, Integer, String, TIMESTAMP, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine

import json
import os
from time import time
from hashlib import md5
import boto3
import logging

_logger = logging.getLogger()
_logger.setLevel(logging.INFO)

def get_engine() -> Engine:
    _logger.info('GET_ENGINE')
    stage = os.getenv('STAGE')
    parameter_path = "/{}/rds/postgres/".format(stage)
    client = boto3.client('ssm')
    response_username = client.get_parameter(
        Name=parameter_path + "username",
        WithDecryption=False)
    response_password = client.get_parameter(
        Name=parameter_path + "password",
        WithDecryption=True)
    _logger.info('GET CREDS')
    username = response_username.get('Parameter', {}).get('Value', None)
    password = response_password.get('Parameter', {}).get('Value', None)

    if not username or not password:
        return -1

    _logger.info('GET ENVS')
    host = os.getenv('DATABASE_ENDPOINT_ADDRESS')
    port = os.getenv('DATABASE_ENDPOINT_PORT')
    _logger.info('Creating engine')
    engine = create_engine(
        'postgresql://{}:{}@{}:{}/Dataplattform'.format(username, password, host, port), echo=False)
    _logger.info('Created engine')
    return engine


_Base = declarative_base()
_engine = get_engine()
Session = sessionmaker(bind=_engine)


def create_tables():
    _logger.info('Creating tables')
    Event.__table__.drop(_engine)
    _Base.metadata.create_all(_engine)
    _logger.info('Tables created')


def _gencode():
    t = str(time()).encode('utf-8')
    h = md5(t).hexdigest()
    return h[:5]


class Event(_Base):
    __tablename__ = 'eventbox_service_events'

    id = Column(Integer, primary_key=True)
    eventname = Column(String(length=255))
    creator = Column(String(length=255))
    start = Column(TIMESTAMP)
    end = Column(TIMESTAMP)
    eventcode = Column(String(length=5), default=_gencode, unique=True)
    active = Column(Boolean)

import json
import os
from datetime import datetime

import boto3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from yr_hour import WeatherHour


def handler(event, context):
    data = process(event)

    return {
            'statusCode': 200,
            'body': data
        }


def insert_data(session, location, location_name, time_from, time_to,
                precipitation, wind_speed, temperature, air_pressure):

    yr_insertion = WeatherHour(
        time=datetime.now().timestamp(),
        location=location,
        location_name=location_name,
        time_from=time_from,
        time_to=time_to,
        precipitation=precipitation,
        wind_speed=wind_speed,
        temperature=temperature,
        air_pressure=air_pressure
    )

    session.add(yr_insertion)
    session.commit()


def process(event):
    # Fetch all data from s3 first to insert all data in one DB-Session
    data = {}
    for record in event.get('Records', []):
        new_dict = get_data_from_s3(record.get('s3', {}).get('bucket', {}).get('name', None),
                                    record.get('s3', {}).get('object', {}).get('key', None))
        if new_dict:
            data.update(json.loads(new_dict))

    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    for key, weather_data in data.items():
        insert_data(session, weather_data.get('location', None), weather_data.get('location_name', None),
                    weather_data.get('time_from', None), weather_data.get('time_to', None),
                    weather_data.get('precipitation', None), weather_data.get('wind_speed', None),
                    weather_data.get('temperature', None), weather_data.get('air_pressure', None))
    process_data(data)
    session.close()
    return data


def process_data(data):
    print("DATA:", data)


def get_data_from_s3(bucket, object):
    if not bucket and not object:
        return None
    client = boto3.client('s3')
    response = client.get_object(
        Bucket=bucket,
        Key=object)

    return response['Body'].read().decode('utf-8')


def get_engine():
    stage = os.getenv('STAGE')
    parameter_path = "/{}/rds/postgres/".format(stage)
    client = boto3.client('ssm')
    response_username = client.get_parameter(
        Name=parameter_path + "username",
        WithDecryption=False)
    response_password = client.get_parameter(
        Name=parameter_path + "password",
        WithDecryption=True)

    username = response_username.get('Parameter', {}).get('Value', None)
    password = response_password.get('Parameter', {}).get('Value', None)

    if not username or not password:
        return -1

    host = os.getenv('DATABASE_ENDPOINT_ADDRESS')
    port = os.getenv('DATABASE_ENDPOINT_PORT')
    engine = create_engine('postgresql://{}:{}@{}:{}/Dataplattform'.format(username, password, host, port), echo=False)
    if not engine.dialect.has_table(engine, 'weather'):
        create_table(engine)
    return engine


def create_table(engine):
    WeatherHour.__table__.create(engine)


def drop_table(engine):
    WeatherHour.__table__.drop(engine)


def get_all_data(session):
    # Returns list of yr_hour for all objects in table
    return session.query(WeatherHour).all()


if __name__== "__main__":
    handler(None, None)
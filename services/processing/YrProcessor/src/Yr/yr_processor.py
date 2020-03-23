import json
import os
from datetime import datetime

import boto3
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session

from yr_hour import WeatherHour

from typing import List, Dict


def handler(event, context):
    data = process(event)

    return {
        'statusCode': 200,
        'body': 'Success'
    }


def process(event):
    # Fetch all data from s3 first to insert all data in one DB-Session
    data = []
    for record in event.get('Records', []):
        new_dict = get_data_from_s3(record.get('s3', {}).get('bucket', {}).get('name', None),
                                    record.get('s3', {}).get('object', {}).get('key', None))
        if new_dict:
            data.append(json.loads(new_dict))

    engine = get_engine()
    WeatherHour.metadata.create_all(bind=engine, checkfirst=True)
    session = sessionmaker(bind=engine)()
    process_data(data, session)
    session.close()


def process_data(weather_data: List[Dict], session: Session):
    insert_rows = []
    for element in weather_data:
        timestamp = element.get('metadata').get('timestamp')
        insert_rows.extend([
            WeatherHour(
                time=timestamp,
                location=data.get('location'),
                location_name=data.get('location_name'),
                time_from=data.get('time_from'),
                time_to=data.get('time_to'),
                precipitation=data.get('precipitation'),
                wind_speed=data.get('wind_speed'),
                temperature=data.get('temperature'),
                air_pressure=data.get('air_pressure')
            )
            for data in element.get('data').values()
        ])

    session.add_all(insert_rows)
    session.commit()


def get_data_from_s3(bucket, object):
    if not bucket and not object:
        return None
    client = boto3.client('s3')
    response = client.get_object(
        Bucket=bucket,
        Key=object)

    return response['Body'].read().decode('utf-8')


def get_engine() -> Engine:
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
    return engine


def get_all_data(session):
    # Returns list of yr_hour for all objects in table
    return session.query(WeatherHour).all()


if __name__ == "__main__":
    handler(None, None)

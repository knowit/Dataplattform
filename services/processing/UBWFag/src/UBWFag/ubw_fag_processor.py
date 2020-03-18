import boto3
import json
from os import environ
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from models import UBWFagtimer
from typing import Dict, List
import pandas as pd
import numpy as np
from datetime import datetime


def handler(event, context):
    process(event)
    return {'statusCode': 200, 'body': 'Success'}


def process(event):
    # Fetch all data from s3 first to insert all data in one DB-Session
    data = [
        get_data_from_s3(record.get('s3', {}).get('bucket', {}).get('name', None),
                         record.get('s3', {}).get('object', {}).get('key', None))
        for record in event.get('Records', [])
    ]
    data = [json.loads(d) for d in data if d]
    if len(data) == 0:
        return

    engine = get_engine()
    UBWFagtimer.metadata.create_all(bind=engine, checkfirst=True)
    session = sessionmaker(bind=engine)()
    process_data(data, session)
    session.close()


def process_data(data: List[List[Dict]], session: Session):
    data = np.hstack(data)
    df = pd.DataFrame.from_records(data)

    # Get unique reg_periods where used_hrs are largest
    df = df[['reg_period', 'used_hrs']].sort_values(['used_hrs']).groupby('reg_period').first().reset_index()

    # Table will never be very large so just get everything
    rows = session.query(UBWFagtimer).all()

    # Remove already inserted periods
    df = df[~df.reg_period.isin([x.reg_period for x in rows])]

    now = datetime.now().time()
    insert_rows = [
        UBWFagtimer(
            time=now,
            reg_period=d.reg_period,
            used_hours=float(d.used_hrs)
        )
        for _, d in df.iterrows()
    ]
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
    stage = environ.get('STAGE')
    if stage == 'LocalDev':
        return create_engine('sqlite:///db.sqlite')

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

    host = environ.get('DATABASE_ENDPOINT_ADDRESS')
    port = environ.get('DATABASE_ENDPOINT_PORT')
    engine = create_engine(
        'postgresql://{}:{}@{}:{}/Dataplattform'.format(username, password, host, port), echo=False)
    return engine


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser('')
    parser.add_argument('--bucket')
    parser.add_argument('--key')
    args = parser.parse_args()
    handler({'Records': [
        {
            's3': {
                'bucket': {'name': args.bucket},
                'object': {'key': args.key}
            }
        }
    ]}, None)

import json
import os
import boto3
import time
from sqlalchemy import create_engine
from sqlalchemy import Column, BigInteger, String
from sqlalchemy.ext.declarative import declarative_base


def handler(event, context):

    process(event)

    return {
        'statusCode': 200,
        'body': 'Success'
    }


def process(event):
    # Fetch all data from s3 first to insert all data in one DB-Session
    data = {}
    for record in event.get('Records', []):
        new_dict = get_data_from_s3(record.get('s3', {}).get('bucket', {}).get('name', None),
                                    record.get('s3', {}).get('object', {}).get('key', None))
        if new_dict:
            data.update(json.loads(new_dict))

    # engine = get_engine()
    # create_table(engine)
    # drop_table(engine)
    #
    # Session = sessionmaker(bind = engine)
    # session = Session()
    # insert_data(session, "test_id", "test_event_summary", "test_creator", 0, 0)
    process_data(data)
    # print(vars(get_all_data(session)[0]))
    # session.close()


def process_data(data):
    # Fetch google events from db for the next 24 hours
    # Compare s3 data with db data
    # If event from s3 does not exist in db then insert into db
    # Else if event has same Id but different attributes insert again DO NOT DELETE PREVIOUS EVENT
    # Else do nothing
    #
    # Reference: https://github.com/knowit/Dataplattform/tree/master/services/structured_mysql/update
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
    engine = create_engine(
        'postgresql://{}:{}@{}:{}/Dataplattform'.format(username, password, host, port), echo=False)
    return engine


def create_table(engine):
    Events.__table__.create(engine)


def drop_table(engine):
    Events.__table__.drop(engine)


def insert_data(session, id, event_summary, creator, start, end):

    event = Events(
        id=id,
        created_timestamp=time.time(),
        event_summary=event_summary,
        creator=creator,
        start_timestamp=start,
        end_timestamp=end)

    session.add(event)
    session.commit()


def get_all_data(session):
    # Returns list of Events for all objects in table
    return session.query(Events).all()


Base = declarative_base()


class Events(Base):
    __tablename__ = 'events'

    id = Column(String(100), primary_key=True)
    created_timestamp = Column(BigInteger, primary_key=True)
    event_summary = Column(String(255))
    creator = Column(String(255))
    start_timestamp = Column(BigInteger)
    end_timestamp = Column(BigInteger)


if __name__ == "__main__":
    handler(None, None)

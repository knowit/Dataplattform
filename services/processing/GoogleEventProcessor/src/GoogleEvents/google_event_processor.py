import boto3
import json
import os
import boto3
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, BigInteger, Integer, String, MetaData, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

def handler(event, context):
#	data = {}
#	for record in event['Records']:
#		data.update(get_data_from_s3(record['s3']['object']['key']))

	engine = get_engine()

#	drop_table(engine)
#	create_table(engine)
#	
#	Session = sessionmaker(bind = engine)
#	session = Session()
#
#	insert_data(session, "aaaaa", "My event", "bartek.kek@knowit.no", 111111111, 10000000, "aaaaa")
#	print(get_all_data(session)[0].version)
#	
#	session.close()

def get_data_from_s3(name):
	client = boto3.client('s3')
	response = client.get_object(
		Bucket='dataplattform-eventbox-bucket',
		Key=name)

	return response['Body'].read().decode('utf-8')


def get_engine():
	# VIL EGENTLIG HA DETTE, MEN MÅ ORDNE NOE MED VPC OG NOE GREIER ¯\_(ツ)_/¯
#	stage = os.getenv('STAGE')
#	parameter_path = "/{}/rds/postgres/".format(stage)
#	client = boto3.client('ssm')
#	response_username = client.get_parameter(
#		Name=parameter_path + "username",
#		WithDecryption=False)
#	response_password = client.get_parameter(
#		Name=parameter_path + "password", 
#		WithDecryption=True)
#
#	username = response_username['Parameter']['Value']
#	password = response_password['Parameter']['Value']


	username = os.getenv('DATABASE_USERNAME')
	password = os.getenv('DATABASE_PASSWORD')
	host = os.getenv('DATABASE_ENDPOINT_ADDRESS')
	port = os.getenv('DATABASE_ENDPOINT_PORT')
	engine = create_engine('postgresql://{}:{}@{}:{}/Dataplattform'.format(username, password, host, port), echo=False)
	return engine


def create_table(engine):
	Events.__table__.create(engine)


def drop_table(engine):
	Events.__table__.drop(engine)


def insert_data(session, id, event_summary, creator, start, end, event_code, active=False):
	
	event = Events(
		id=id, 
		event_summary=event_summary, 
		creator=creator, 
		start=start, 
		end=end, 
		event_code=event_code, 
		active=active)
	
	session.add(event)
	session.commit()


def get_all_data(session):
	return session.query(Events).all()


Base = declarative_base()

class Events(Base):
	__tablename__ = 'events'

	id = Column(String(100), primary_key = True)
	version = Column(Integer, primary_key = True, autoincrement=True)
	event_summary = Column(String(255))
	creator = Column(String(255))
	start = Column(BigInteger)
	end = Column(BigInteger)


class Events_Status(Base):
	__tablename__ = 'events_status'

	id = Column(String(100), primary_key = True)


if __name__== "__main__":
	handler(None, None)
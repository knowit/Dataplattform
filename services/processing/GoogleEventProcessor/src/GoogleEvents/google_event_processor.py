import boto3
import json
import os
import boto3
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, BigInteger, Integer, String, MetaData, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

def handler(event, context):
	# Fetch all data from s3 first to insert all data in one DB-Session
#	data = {}
#	for record in event['Records']:
#		data.update(record['s3']['bucket']['name'], get_data_from_s3(record['s3']['object']['key']))

	engine = get_engine()
#	drop_table(engine)
#
#	Session = sessionmaker(bind = engine)
#	session = Session()
#	process_data(data)
#	session.close()


def process_data(data):
###########################################TODO#####################################################
#	Fetch google events from db for the next 24 hours
#	Compare s3 data with db data
#	If event from s3 does not exist in db then insert into db
#	Else if event has same Id but different attributes insert again DO NOT DELETE PREVIOUS EVENT
#	Else do nothing
#	
#	Reference: https://github.com/knowit/Dataplattform/tree/master/services/structured_mysql/update
####################################################################################################
	print("Function can't be empty")


def get_data_from_s3(bucket, object):
	client = boto3.client('s3')
	response = client.get_object(
		Bucket=bucket,
		Key=object)

	return response['Body'].read().decode('utf-8')


def get_engine():
#	VIL EGENTLIG HA DETTE, MEN MÅ ORDNE NOE MED VPC OG NOE GREIER ¯\_(ツ)_/¯
#	https://stackoverflow.com/questions/52134100/parameter-store-request-timing-out-inside-of-aws-lambda -- Tror dette er problemet
#
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
	# Returns list of Events for all objects in table
	return session.query(Events).all()


Base = declarative_base()

class Events(Base):
	__tablename__ = 'events'

	id = Column(String(100), primary_key = True)
	created_timestamp = Column(BigInteger, primary_key = True)
	event_summary = Column(String(255))
	creator = Column(String(255))
	start_timestamp = Column(BigInteger)
	end_timestamp = Column(BigInteger)
	



if __name__== "__main__":
	handler(None, None)
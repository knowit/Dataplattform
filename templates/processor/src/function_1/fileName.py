import boto3
import json
import os
import boto3
import time
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, BigInteger, Integer, String, MetaData, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

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

#	engine = get_engine()
#	Session = sessionmaker(bind = engine)
#	session = Session()
	process_data(data)
#	session.close()

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
	return engine


if __name__== "__main__":
	handler(None, None)
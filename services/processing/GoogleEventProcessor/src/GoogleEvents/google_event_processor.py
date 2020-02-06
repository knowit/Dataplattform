import boto3
import json

def handler(event, context):
	for record in event['Records']:
		main(record['s3']['object']['key'])


def main(name):
	client = boto3.client('s3')
	response = client.get_object(
		Bucket='dataplattform-eventbox-bucket',
		Key=name)

	data = response['Body'].read().decode('utf-8')



if __name__== "__main__":
	handler()

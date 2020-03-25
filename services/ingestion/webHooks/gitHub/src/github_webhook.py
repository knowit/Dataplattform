import boto3
import os
import time
import json
import hmac
import hashlib


def handler(event, context):
    body = event["body"]
    headers = event["headers"]

    if "X-Hub-Signature" not in headers:
        return {
            'statusCode': 403,
            'body': json.dumps({"reason": "No signature"})
        }

    received_signature = headers["X-Hub-Signature"]
    if validate_payload_signature(body, received_signature):
        data = json.loads(body)
        if data.get('repository').get('private') is False:
            insert_data(data, headers['X-GitHub-Event'])
        return{
            'statusCode': 200,
            'body': 'Success'
        }
    else:
        return{
            'statusCode': 403,
            'body': json.dumps({'reason': 'Invalid signature'})
        }


def validate_payload_signature(body, received_signature):
    rec_sig = received_signature.split("=")
    if rec_sig[0] != "sha1":
        return False

    client = boto3.client('ssm')
    secret = client.get_parameter(
        Name=os.getenv('GITHUB_SECRET'),
        WithDecryption=True)
    shared_secret = secret['Parameter']['Value']

    calculated_signature = hmac.new(shared_secret.encode(), body.encode(),
                                    hashlib.sha1).hexdigest()
    return hmac.compare_digest(calculated_signature, rec_sig[1])


def insert_data(data, event):

    data = {
        'metadata': {
            'timestamp': time.time(),
            'event': event
        },
        'data': data
    }

    path = os.getenv("ACCESS_PATH")

    s3 = boto3.resource('s3')
    s3_object = s3.Object(os.getenv('DATALAKE'), f'{path}{event}/{str(int(time.time()))}.json')
    s3_object.put(Body=(bytes(json.dumps(data).encode('UTF-8'))))

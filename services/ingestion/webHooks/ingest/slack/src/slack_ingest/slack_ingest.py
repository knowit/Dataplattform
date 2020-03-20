import boto3
import os
import time
import json
import hmac
import hashlib


def handler(event, context):
    status = verify_slack_event(event)
    if status == 1:
        data = json.loads(event['body'])
        if data['type'] == 'url_verification':
            return {
                'statusCode': 200,
                'body': json.dumps({'challenge': data['challenge']})
            }
        else:
            insert_data(data)
    elif status == 0:
        return {
            'statusCode': 403,
            'body': json.dumps({"reason": "No signature"})
        }
    elif status == -1:
        return {
            'statusCode': 403,
            'body': json.dumps({"reason": "Invalid signature"})
        }


def insert_data(data):
    data = {
        'metadata': int(time.time()),
        'data': data
    }

    path = os.getenv("ACCESS_PATH")
    s3 = boto3.resource('s3')
    s3_object = s3.Object(os.getenv('DATALAKE'),
                          '{}{}/{}.json'.format(path, data['data']['event']['type'], str(int(time.time()))))
    s3_object.put(Body=(bytes(json.dumps(data).encode('UTF-8'))))


def verify_slack_event(event):
    body = event["body"]
    headers = event["headers"]

    if ("X-Slack-Signature" not in headers) or ("X-Slack-Request-Timestamp" not in headers):
        return -0

    received_signature = headers["X-Slack-Signature"]
    slack_timestamp = headers["X-Slack-Request-Timestamp"]
    client = boto3.client('ssm')
    shared_secret = client.get_parameter(
        Name='/dev/web-hook/slack/signing-secret',
        WithDecryption=True)
    secret_from_ssm = shared_secret['Parameter']['Value']

    if validate_payload_signature(body, received_signature, slack_timestamp, secret_from_ssm):
        return 1
    else:
        return -1


def validate_payload_signature(body, received_signature, slack_timestamp, shared_secret):
    """
    As described by https://api.slack.com/docs/verifying-requests-from-slack
    """
    basestring = 'v0:{}:{}'.format(slack_timestamp, body.strip()).encode()
    calculated_signature = 'v0={}'.format(hmac.new(shared_secret.encode(), basestring,
                                          hashlib.sha256).hexdigest())
    return hmac.compare_digest(calculated_signature, received_signature)

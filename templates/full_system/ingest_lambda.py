from dataplattform.common.handler import Handler
from dataplattform.common.schema import Data, Metadata
from datetime import datetime
import pandas as pd
from typing import Dict
import boto3
from os import environ
import json

handler = Handler()


@handler.ingest()
def ingest(event) -> Data:

    sqs_queue_name = environ['SQS_QUEUE_NAME']
    sqs_client = boto3.client('sqs')
    response = sqs_client.get_queue_url(QueueName=sqs_queue_name)
    sqs_url = response['QueueUrl']
    timestamp_now = int(datetime.now().timestamp())
    message_response = sqs_client.send_message(QueueUrl=sqs_url, MessageBody=str(timestamp_now) + '.json',
                                               MessageGroupId="messageGroup1")

    d = [{'test': 'This is a test message', 'id': 1}, {'test': 'This is also a test message', 'id': 2}]
    return Data(
        metadata=Metadata(timestamp=int(timestamp_now)),
        data=d)

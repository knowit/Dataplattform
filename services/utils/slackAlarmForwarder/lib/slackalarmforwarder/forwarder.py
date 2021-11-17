import boto3
from cachetools import cached, TTLCache
from os import environ
import requests
import json

ssm_client = boto3.client('ssm')

ssm_name_base = f'/{environ.get("STAGE")}/{environ.get("SERVICE")}'
slack_callback_url_ssm_name = f'{ssm_name_base}/{environ.get("SLACK_CALLBACK_SSM_NAME")}'


@cached(cache=TTLCache(maxsize=1, ttl=1200))
def slack_callback_url():
    return ssm_client.get_parameter(
        Name=slack_callback_url_ssm_name,
        WithDecryption=False
    ).get('Parameter', {}).get('Value', None)


def create_payload(msg):
    colors = dict(OK='good', INSUFFICIENT_DATA='warning', ALARM='danger')

    return {
        'mrkdwn_in': ['text'],
        'title': f"{msg['Region']} -- {msg['AlarmName']}",
        'title_link': f"https://{msg['AWSAccountId']}.signin.aws.amazon.com/console/cloudwatch",
        'text': f"Alarm `{msg['AlarmName']}` is in state `{msg['NewStateValue']}`\n\n{msg['NewStateReason']}",
        'color': colors.get(msg['NewStateValue'], '#bfbfbf'),
        'footer': 'Dataplattform <3'
    }


def handler(event, context):
    attachments = []
    for record in event.get('Records', []):
        msg = record.get('Sns', {}).get('Message', "")
        if msg:
            attachments.append(create_payload(json.loads(msg)))

    requests.post(
        url=slack_callback_url(),
        json=dict(attachments=attachments)
    )
    return dict(status_code=200, body="")


if __name__ == '__main__':
    with open('test_event.json') as f:
        event = json.loads(f.read())
        handler(event, None)

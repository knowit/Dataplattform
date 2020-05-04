from dataplattform.common.handler import Handler, Response
from dataplattform.common.schema import Data, Metadata
from dataplattform.common.aws import SSM
from json import loads, dumps
from typing import Dict, Union
from datetime import datetime
import pandas as pd
import numpy as np
import hmac
import hashlib
import re
import requests


handler = Handler()


@handler.validate()
def validate(event) -> Union[bool, Response]:
    body = event["body"]
    headers = event["headers"]

    if ("X-Slack-Signature" not in headers) or ("X-Slack-Request-Timestamp" not in headers):
        return False

    received_signature = headers["X-Slack-Signature"]
    slack_timestamp = headers["X-Slack-Request-Timestamp"]
    shared_secret = SSM(with_decryption=True).get('slack_signing_secret')

    base_string = 'v0:{}:{}'.format(slack_timestamp, body.strip()).encode()
    calculated_signature = 'v0={}'.format(hmac.new(shared_secret.encode(), base_string,
                                                   hashlib.sha256).hexdigest())
    valid_signature = hmac.compare_digest(
        calculated_signature, received_signature)
    if not valid_signature:
        return False

    data = loads(event['body'])
    if data['type'] == 'url_verification':
        return Response(body=dumps({'challenge': data['challenge']}))

    return True


@handler.ingest()
def ingest(event) -> Union[Data, Response]:
    def remove_emoji_modifiers(emoji):
        return re.sub(r'::skin-tone-.', '', emoji)

    def get_channel_name(channel):
        slack_token = SSM(with_decryption=True).get('slack_app_token')
        res = requests.get(
            'https://slack.com/api/channels.info',
            headers={'Authorization': f'Bearer {slack_token}'},
            params={'channel': channel})
        return res.json().get('channel', {}).get('name', None)

    data = loads(event['body'])

    slack_event = data['event']
    channel = slack_event.get(
        'channel', slack_event.get('item', {}).get('channel', ''))
    event_type = slack_event['type']

    if not channel.startswith('C') or \
            slack_event.get('subtype', '') == 'bot_message' or \
            event_type not in ['reaction_added', 'message']:
        return Response()

    channel_name = get_channel_name(channel)

    if event_type == 'reaction_added':
        event_data = [{
            'event_type': event_type,
            'channel': channel,
            'channel_name': channel_name,
            'event_ts': data['event_time'],
            'team_id': data['team_id'],
            'emoji': remove_emoji_modifiers(slack_event['reaction']),
        }]
    else:
        emoji_list = [
            remove_emoji_modifiers(inner_element.get('name'))
            for block in slack_event.get('blocks', [])
            for element in block.get('elements', [])
            for inner_element in element.get('elements', [])
            if inner_element.get('type', '') == 'emoji'
        ]

        event_data = [
            {
                'event_type': event_type,
                'channel': channel,
                'channel_name': channel_name,
                'event_ts': data["event_time"],
                'team_id': data["team_id"],
                'emoji': emoji,
            }
            for emoji in emoji_list]

    if not event_data:
        return Response()

    return Data(
        metadata=Metadata(
            timestamp=datetime.now().timestamp(),
        ),
        data=event_data
    )


@handler.process(partitions={'slack_emoji': ['event_type']})
def process(data) -> Dict[str, pd.DataFrame]:
    data = [
        [dict(x, time=d['metadata']['timestamp']) for x in d['data']]
        for d in [d.json() for d in data]
    ]

    data = np.hstack(data)
    df = pd.DataFrame.from_records(data)

    return {
        'slack_emoji': df,
    }

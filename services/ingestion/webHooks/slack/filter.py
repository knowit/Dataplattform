import re
import requests
from os import environ
import boto3


def remove_emoji_modifiers(emoji):
    return re.sub(r'::skin-tone-.', '', emoji)


def get_channel_name(channel):
    stage = environ.get('STAGE')
    parameter_path = "/{}/web-hook/slack/".format(stage)
    client = boto3.client('ssm')
    response_slack_token = client.get_parameter(
        Name=parameter_path + "app-token",
        WithDecryption=False)

    slack_token = response_slack_token.get('Parameter', {}).get('Value', None)

    headers = {
        'Authorization': f'Bearer {slack_token}',
    }
    params = {
        'channel': channel
    }
    url = 'https://slack.com/api/channels.info'
    res = requests.get(url, headers=headers, params=params)
    try:
        return res.json().get('channel').get('name')
    except Exception:
        return None


def filter_slack_event(data):
    event = data.get('event', None)
    if not event:
        return []

    channel = event.get('channel') or event.get('item', {}).get('channel') or ''

    # All public channels starts with C
    if not channel.startswith('C'):
        return []

    if event.get('subtype', '') == 'bot_message':
        return[]

    event_type = event.get('type')
    channel_name = get_channel_name(channel)
    filtered_data = {
        'event': {
            'type': event_type,
            'channel': channel,
            'channel_name': channel_name,
            'event_ts': event.get('event_ts')
        },
        'team_id': data.get('team_id'),
    }
    events = []
    if event_type == 'reaction_added':
        filtered_data['event']['reaction'] = remove_emoji_modifiers(event.get('reaction'))

    elif event_type == 'message':
        emoji_list = [
            remove_emoji_modifiers(inner_element.get('name'))
            for block in event.get('blocks', [])
            for element in block.get('elements', [])
            for inner_element in element.get('elements', [])
            if inner_element.get('type', '') == 'emoji'
        ]

        [events.append(
            {
                'event': {
                    'type': 'emoji_added',
                    'channel': event.get("channel"),
                    'channel_name': channel_name,
                    'emoji': emoji
                },
                'event_ts': data.get("event_time"),
                'team_id': data.get("team_id")
            }
        ) for emoji in emoji_list]

    events.append(filtered_data)
    return events

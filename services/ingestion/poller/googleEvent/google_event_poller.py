from dataplattform.common.handler import Handler
from dataplattform.common.schema import Data, Metadata
from dataplattform.common.aws import SSM
import googleapiclient.discovery
import httplib2
from oauth2client.service_account import ServiceAccountCredentials
import json
from datetime import datetime

import pandas as pd
from typing import Dict

handler = Handler()


@handler.ingest()
def ingest(event) -> Data:
    return Data(metadata=Metadata(timestamp=datetime.now().timestamp()), data=poll())


@handler.process(partitions={'google_calender_event': []}) # TODO: Replace with {} after rebase
def process(data) -> Dict[str, pd.DataFrame]:
    def make_dataframe(d):
        d = d.json()
        metadata, payload = d['metadata'], d['data']
        df = pd.json_normalize(payload.values())
        df['time'] = int(metadata['timestamp'])
        return df

    df_new = pd.concat([make_dataframe(d) for d in data])
    return {
        'google_calender_event': df_new
    }


# returns a dict of dicts 
def poll():
    credentials_from_ssm, calendar_ids_from_ssm = SSM(with_decryption=False).get('credentials', 'calendarIds')

    events = {}

    for calendar_id in calendar_ids_from_ssm:
        events.update(get_events(credentials_from_ssm, calendar_id))

    return events


def get_events(credsentials_from_env, calendar_id):
    """
    :param creds: credentials
    :param calendar_id:
    :return: A dictionary containing (max 10) of the events in the nearest future from this
    specific calendar_id.
    """

    credsentials_json = json.loads(credsentials_from_env)
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(credsentials_json, [
        'https://www.googleapis.com/auth/calendar.readonly'])

    http = httplib2.Http()
    http = credentials.authorize(http)
    service = googleapiclient.discovery.build(
        serviceName='calendar', version='v3', http=http, cache_discovery=False)
    now = datetime.utcnow().isoformat() + '+02:00'
    tomorrow = datetime.utcfromtimestamp(datetime.now().timestamp() + (
        60 * 60 * 24)).isoformat() + '+02:00'
    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=now,
        timeMax=tomorrow,
        timeZone='UTC+0:00',
        singleEvents=True,
        orderBy='startTime') \
        .execute()
    events = events_result.get('items', [])
    info = {}
    for event in events:
        boxes = []
        if 'location' in event:
            temp = event['location'].split(',')
            for box in temp:
                if "Enheter" in box:
                    boxes.append(box.split('-')[-1])

        startTime = ""
        endTime = 0
        if "dateTime" in event['start']:
            startTime = get_timestamp(event['start']['dateTime'])
        else:
            timeObject = list(map(int, event['start']['date'].split("-")))
            startTime = datetime.timestamp(
                datetime(timeObject[0], timeObject[1], timeObject[2]))
        if "dateTime" in event['end']:
            endTime = get_timestamp(event['end']['dateTime'])
        else:
            timeObject = list(map(int, event['end']['date'].split("-")))
            endTime = datetime.timestamp(datetime(
                timeObject[0], timeObject[1], timeObject[2]))

        summary = ""
        if "summary" in event:
            summary = event["summary"]

        creator = ""
        if "creator" in event:
            creator = event['creator']['email']

        info[event['id']] = {
            'event_id': event['id'],
            'calendar_id': calendar_id,
            'timestamp_from': startTime,
            'timestamp_to': endTime,
            'event_summary': summary,
            'event_button_names': boxes,
            'creator': creator,
        }
    return info


def get_timestamp(date):
    return datetime.fromisoformat(date).timestamp()


if __name__ == "__main__":
    poll()

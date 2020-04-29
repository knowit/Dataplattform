from dataplattform.common.handler import Handler
from dataplattform.common.schema import Data, Metadata
from dataplattform.common.aws import SSM
import googleapiclient.discovery
import httplib2
from oauth2client.service_account import ServiceAccountCredentials
import json
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict

handler = Handler()


@handler.ingest()
def ingest(event) -> Data:

    def get_event_data():
        credentials_from_ssm, calendar_ids_from_ssm = SSM(with_decryption=False).get('credentials', 'calendarIds')
        events = {}
        for calendar_id in calendar_ids_from_ssm:
            events.update(get_events_from_calendar(credentials_from_ssm, calendar_id))
        return events

    def get_events_from_calendar(credentials_from_env, calendar_id):
        """
        :param creds: credentials
        :param calendar_id:
        :return: A dictionary containing (max 10) of the events in the nearest future from this
        specific calendar_id.
        """
        service = get_calender_service(credentials_from_env)

        now = datetime.now()
        tomorrow = datetime.now() + timedelta(days=1)

        events = get_event_list_in_interval(service, now, tomorrow, calendar_id)
        info = {}

        for event in events:
            info[event['id']] = get_event_info(event, calendar_id)

        return info

    def get_calender_service(credentials_from_env):
        credsentials_json = json.loads(credentials_from_env)
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(credsentials_json, [
            'https://www.googleapis.com/auth/calendar.readonly'])

        http = httplib2.Http()
        http = credentials.authorize(http)
        service = googleapiclient.discovery.build(
            serviceName='calendar', version='v3', http=http, cache_discovery=False)
        return service

    def get_event_list_in_interval(service, startDate, endDate, calendar_id):
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=startDate,
            timeMax=endDate,
            timeZone='UTC+0:00',
            singleEvents=True,
            orderBy='startTime') \
            .execute()
        events = events_result.get('items', [])
        return events

    def get_event_info(event, calendar_id):

        temp = event.get('location', '').split(',')
        boxes = [box.split('-')[-1] for box in temp if 'Enheter' in box]

        startTime = get_time_from_event_time(event['start'])
        endTime = get_time_from_event_time(event['end'])

        event_info = {
                'event_id': event['id'],
                'calendar_id': calendar_id,
                'timestamp_from': startTime,
                'timestamp_to': endTime,
                'event_summary': event.get('summary', ''),
                'event_button_names': boxes,
                'creator': event.get('creator', ''),
            }
        return event_info

    return Data(metadata=Metadata(timestamp=datetime.now().timestamp()), data=get_event_data())


@handler.process(partitions={'google_calender_event': []})  # TODO: Replace with {} after rebase
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


def get_time_from_event_time(start_or_end_time):
    if "dateTime" in start_or_end_time:
        new_time = get_timestamp(start_or_end_time['dateTime'])
    else:
        new_time = get_datetime_from_date(start_or_end_time)
    return new_time


def get_datetime_from_date(start_or_end_date):
    timeObject = list(map(int, start_or_end_date['date'].split("-")))
    new_time = datetime.timestamp(
        datetime(timeObject[0], timeObject[1], timeObject[2]))
    return new_time


def get_timestamp(date):
    return datetime.fromisoformat(date).timestamp()

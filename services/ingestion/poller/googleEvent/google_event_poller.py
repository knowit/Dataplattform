from dataplattform.common.handler import Handler
from dataplattform.common.schema import Data, Metadata
from dataplattform.common.aws import SSM
from botocore.exceptions import ClientError

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

    def get_event_data():
        credentials_from_ssm, calendar_ids_from_ssm = SSM(with_decryption=False).get('credentials', 'calendarIds')
        calendar_ids_from_ssm = calendar_ids_from_ssm.split(',')
        service = get_calender_service(credentials_from_ssm)

        events = []

        for calendar_id in calendar_ids_from_ssm:
            for event in get_events_from_calendar(service, calendar_id):
                events.append(event)
        return events

    def get_events_from_calendar(service, calendar_id):
        """
        :param service: google calendar
        :param calendar_id: unique calendar id
        :return: A dictionary containing the latest events from a specific calendar_id.
        """

        sync_token_ssm_name = ('sync_token_' + calendar_id).replace('@', '-', 1)
        print('sync_token_name:', sync_token_ssm_name)
        try:
            sync_token = SSM(with_decryption=False).get(sync_token_ssm_name)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ParameterNotFound':
                sync_token = ''
            else:
                raise e

        events, new_sync_token = sync_events(service, calendar_id, sync_token)
        SSM(with_decryption=True).put(name=sync_token_ssm_name,
                                      value='',
                                      value_type='String',
                                      overwrite=True)
        return events

    def get_calender_service(credentials_from_env):
        credsentials_json = json.loads(credentials_from_env)
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(credsentials_json, [
            'https://www.googleapis.com/auth/calendar.readonly'])

        http = httplib2.Http()
        http = credentials.authorize(http)
        service = googleapiclient.discovery.build(
            serviceName='calendar', version='v3', http=http, cache_discovery=False)

        return service

    def sync_events(service, calendar_id, sync_token):

        request_params = {'calendarId': calendar_id,
                          'timeZone': 'UTC+0:00',
                          'singleEvents': True,
                          'orderBy': 'startTime'}
        if not sync_token:
            request_params['timeMin'] = '2020-05-01T00:00:00+00:00'  # TODO: Which date should we start syncing from?
        else:
            request_params['syncToken'] = sync_token

        new_sync_token = ''
        events_for_current_calender = []

        current_request = service.events().list(**request_params)

        while current_request is not None:
            current_page = current_request.execute()
            tmp_events = current_page.get('items', [])
            for event in tmp_events:
                events_for_current_calender.append(get_event_info(event, calendar_id))

            new_sync_token = current_page.get('nextSyncToken', '')
            current_request = service.events().list_next(current_request, current_page)

        return events_for_current_calender, new_sync_token

    # TODO: Check exception safety, can raise?
    def get_event_info(event, calendar_id):

        temp = event.get('location', '').split(',')
        boxes = [box.split('-')[-1] for box in temp if 'Enheter' in box]
        creator_name = dict(event.get('creator', '')).get('email', '')

        event_info = {
                'event_id': event['id'],
                'calendar_id': calendar_id,
                'timestamp_from': get_time_from_event_time(event.get('start', '')),
                'timestamp_to': get_time_from_event_time(event.get('end', '')),
                'event_summary': event.get('summary', ''),
                'event_button_names': boxes,
                'creator': creator_name,
            }
        return event_info

    return Data(metadata=Metadata(timestamp=datetime.now().timestamp()), data=get_event_data())


@handler.process(partitions={})
def process(data) -> Dict[str, pd.DataFrame]:
    def make_dataframe(d):
        d = d.json()
        metadata, payload = d['metadata'], d['data']
        df = pd.json_normalize(payload)
        df['time'] = int(metadata['timestamp'])
        return df

    df_new = pd.concat([make_dataframe(d) for d in data])
    return {
        'google_calender_event': df_new
    }


def get_time_from_event_time(start_or_end_time):
    if 'dateTime' in start_or_end_time:
        return start_or_end_time['dateTime']
    elif 'date' in start_or_end_time:
        return get_datetime_from_date(start_or_end_time).timestamp()
    else:
        return None


def get_datetime_from_date(start_or_end_date):
    timeObject = list(map(int, start_or_end_date['date'].split("-")))
    new_time = datetime(timeObject[0], timeObject[1], timeObject[2])
    return new_time


def get_timestamp(date):
    return datetime.fromisoformat(date).timestamp()

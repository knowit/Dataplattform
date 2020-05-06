from dataplattform.common.handler import Handler
from dataplattform.common.schema import Data, Metadata
from dataplattform.common.aws import SSM

import googleapiclient.discovery
import httplib2
from oauth2client.service_account import ServiceAccountCredentials
from botocore.exceptions import ClientError

import json
from datetime import datetime, timezone
import pandas as pd
from typing import Dict

handler = Handler()


@handler.ingest()
def ingest(event) -> Data:

    def get_event_data():
        credentials_from_ssm, calendar_ids_from_ssm = SSM(with_decryption=False).get('credentials', 'calendarIds')
        service = get_calender_service(credentials_from_ssm)

        all_events = []
        for calendar_id in calendar_ids_from_ssm:
            events_for_current_calendar = get_events_from_calendar(service, calendar_id)
            for cal_event in events_for_current_calendar:
                all_events.append(cal_event)
        return all_events

    def get_events_from_calendar(service, calendar_id):
        """
        :param creds: credentials
        :param calendar_id:
        :return: A dictionary containing the latest events using the sync token
        specific calendar_id.
        """
        sync_token_ssm_name = ('sync_token_' + calendar_id).replace('@', '-', 1)
        sync_token = None

        try:
            sync_token = SSM(with_decryption=False).get(sync_token_ssm_name)
        except ClientError as e:
            if (e.response['Error']['Code'] == 'ParameterNotFound'):
                sync_token = None
            else:
                raise e

        events, new_sync_token = sync_events(service, calendar_id, sync_token)
        SSM(with_decryption=False).put(name=sync_token_ssm_name,
                                       value=new_sync_token,
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

        local_time = datetime.now(timezone.utc).astimezone()
        today = local_time.isoformat()
        request_params = {'calendarId': calendar_id,
                          'singleEvents': True,
                          'timeMax': today}
        if not sync_token:
            request_params['timeMin'] = '2020-05-01T00:00:00+00:00'  # TODO: Fix to 2010-01-01T00:00:00+02:00
        else:
            request_params['syncToken'] = sync_token

        events_for_current_calender = []
        current_request = service.events().list(**request_params)

        # TODO: Check if this is ok, should use pageToken?
        while current_request is not None:
            current_page = current_request.execute()
            tmp_events = current_page.get('items', [])
            for event in tmp_events:
                events_for_current_calender.append(get_event_info(event, calendar_id))

            new_sync_token = current_page.get('nextSyncToken', '')
            current_request = service.events().list_next(current_request, current_page)

        return events_for_current_calender, new_sync_token

    def get_event_info(event, calendar_id):

        temp = event.get('location', '').split(',')
        boxes = [box.split('-')[-1] for box in temp if 'Enheter' in box]
        creator_name = dict(event.get('creator', '')).get('email', '')

        event_info = {
                'event_id': event['id'],
                'calendar_id': calendar_id,
                'timestamp_from': get_time_from_event_time(event['start']),
                'timestamp_to': get_time_from_event_time(event['end']),
                'event_summary': event.get('summary', ''),
                'event_button_names': boxes,
                'creator': creator_name,
            }
        return event_info
    return Data(metadata=Metadata(timestamp=datetime.now().timestamp()), data=get_event_data())


@handler.process(partitions={})  # TODO: Replace with {} after rebase
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
    if "dateTime" in start_or_end_time:
        new_time = start_or_end_time['dateTime']
    else:
        new_time = get_datetime_from_date(start_or_end_time)
    return new_time


def get_datetime_from_date(start_or_end_date):
    timeObject = list(map(int, start_or_end_date['date'].split("-")))
    return datetime(timeObject[0], timeObject[1], timeObject[2])

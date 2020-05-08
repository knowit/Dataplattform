from dataplattform.common.handler import Handler
from dataplattform.common.schema import Data, Metadata
from dataplattform.common.aws import SSM

import googleapiclient.discovery
import googleapiclient.errors as errors
import httplib2
from oauth2client.service_account import ServiceAccountCredentials
from botocore.exceptions import ClientError

import json
from datetime import datetime, timedelta, timezone
from pytz import timezone as pytz_timezone
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
        :return: A dictionary containing the latest events using the latest poll date
        specific calendar_id.
        """
        last_poll_time_ssm_name = ('last_sync_time_' + calendar_id).replace('@', '-', 1)
        last_poll_time = None

        try:
            last_poll_time = SSM(with_decryption=False).get(last_poll_time_ssm_name)
        except ClientError as e:
            if (e.response['Error']['Code'] == 'ParameterNotFound'):
                last_poll_time = None
            else:
                raise e

        events, new_poll_time = sync_events(service, calendar_id, last_poll_time)
        SSM(with_decryption=False).put(name=last_poll_time_ssm_name,
                                       value=new_poll_time,
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

    def sync_events(service, calendar_id, last_poll_time):

        min_date = '2010-01-01T00:00:00+00:00'
        today = datetime.now(timezone.utc)

        request_params = {'calendarId': calendar_id,
                          'singleEvents': True,
                          'showDeleted': False,
                          'orderBy': 'startTime',
                          'timeMax': today.isoformat()}
        if not last_poll_time:  # First time poller is called
            request_params['timeMin'] = min_date
        else:
            last_sync_date = datetime.fromtimestamp(int(last_poll_time))
            last_sync_date_rfc3339 = last_sync_date.astimezone(pytz_timezone("Europe/Oslo"))
            request_params['timeMin'] = last_sync_date_rfc3339.isoformat()

        events_for_current_calender = []
        current_request = service.events().list(**request_params)

        while True:
            current_page = current_request.execute()
            tmp_events = current_page.get('items', [])
            for event in tmp_events:
                events_for_current_calender.append(get_event_info(event, calendar_id))

            page_token = current_page.get('nextPageToken')
            if not page_token:
                break
            current_request = service.events().list_next(current_request, current_page)
        return events_for_current_calender, str(int(today.timestamp()))

    def get_event_info(event, calendar_id):

        temp = event.get('location', '').split(',')
        boxes = [box.split('-')[-1] for box in temp if 'Enheter' in box]
        creator_email = dict(event.get('creator', '')).get('email', '')
        event_timezone = event.get('timeZone', '')

        event_info = {
                'event_id': event['id'],
                'calendar_id': calendar_id,
                'timestamp_from': get_timestamp_from_event_time(event['start'], event_timezone),
                'timestamp_to': get_timestamp_from_event_time(event['end'], event_timezone),
                'event_summary': event.get('summary', ''),
                'event_button_names': boxes,
                'creator': creator_email,
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


def get_timestamp_from_event_time(start_or_end_time, event_timezone_str):
    if 'dateTime' in start_or_end_time:
        new_time_str = start_or_end_time.get('dateTime')
        new_time = datetime.fromisoformat(new_time_str)
        if (event_timezone_str != ''):
            event_timezone = pytz_timezone(event_timezone_str)
            new_time = datetime.fromisoformat(event_timezone.localize(new_time))
    elif 'date' in start_or_end_time:
        new_time = get_datetime_from_date(start_or_end_time)
    else:
        raise KeyError

    return int(new_time.timestamp())


def get_datetime_from_date(start_or_end_date):
    time_object = list(map(int, start_or_end_date['date'].split("-")))
    return datetime(time_object[0], time_object[1], time_object[2])

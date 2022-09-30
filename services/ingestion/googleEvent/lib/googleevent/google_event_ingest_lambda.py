from dataplattform.common.handlers.ingest import IngestHandler
from dataplattform.common.schema import Data, Metadata
from dataplattform.common.aws import SSM

import googleapiclient.discovery
import googleapiclient._auth as auth
from google.oauth2.service_account import Credentials as ServiceAccountCredentials

from botocore.exceptions import ClientError

import json
from datetime import datetime, timedelta, timezone


handler = IngestHandler()


@handler.ingest()
def ingest(event) -> Data:

    def get_event_data():
        """
        :return: A list containing the all latest for the calendar ids stored in SSM
        """
        credentials_from_ssm = SSM(with_decryption=True).get('credentials')
        calendar_ids_from_ssm = SSM(with_decryption=False).get('calendarIds')
        service = get_calender_service(credentials_from_ssm)

        all_events = []
        for calendar_id in calendar_ids_from_ssm:
            events_for_current_calendar = get_events_from_calendar(service, calendar_id)
            for cal_event in events_for_current_calendar:
                all_events.append(cal_event)
        return all_events

    def get_events_from_calendar(service, calendar_id):
        """
        Polls the latest calendar events and updates the poll time in SSM
        :param service: an autorized calendar service
        :param calendar_id: a unique id for a specific calendar
        :return: A dictionary containing the latest events using the latest poll date for a
        specific calendar_id.
        """
        last_poll_time_ssm_name = ('last_poll_time_' + calendar_id).replace('@', '-', 1)
        last_poll_time = None

        try:
            last_poll_time = SSM().get(last_poll_time_ssm_name)
        except ClientError as e:
            if (e.response['Error']['Code'] == 'ParameterNotFound'):
                last_poll_time = None
            else:
                raise e

        events, new_poll_time = sync_events(service, calendar_id, last_poll_time)
        SSM().put(last_poll_time_ssm_name, new_poll_time)
        return events

    def get_calender_service(credentials_from_ssm):
        """
        :param credentials_from_ssm:
        :return: A autorized calendar service using credentials from SSM
        """
        credsentials_json = json.loads(credentials_from_ssm)
        scope = ["https://www.googleapis.com/auth/calendar.readonly"]
        credentials = ServiceAccountCredentials.from_service_account_info(credsentials_json)
        credentials = auth.with_scopes(credentials, scope)
        auth_http = auth.authorized_http(credentials)

        service = googleapiclient.discovery.build(
            serviceName='calendar', version='v3', http=auth_http, cache_discovery=False)

        return service

    def sync_events(service, calendar_id, last_poll_time):
        """
        :param service: an autorized calendar service
        :param last_poll_time: timestamp for the latest poll time for the calendar specified by calendar_id
        :param calendar_id: a unique id for a specific calendar
        :return: A dictionary containing the latest events using the latest poll date for a
        specific calendar_id and the time of this poll
        """
        current_time_zone = timezone(timedelta(hours=2))
        today = datetime.now(tz=current_time_zone)

        request_params = {'calendarId': calendar_id,
                          'singleEvents': True,
                          'showDeleted': False,
                          'orderBy': 'startTime',
                          'timeMax': today.isoformat(),
                          'timeZone': 'Europe/Oslo'}

        if not last_poll_time:  # First time poller is called
            request_params['timeMin'] = datetime(2010, 1, 1, tzinfo=current_time_zone).isoformat()
        else:
            last_poll_date = datetime.fromtimestamp(int(last_poll_time), current_time_zone)
            request_params['timeMin'] = last_poll_date.isoformat()

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
        """
        :param event: a dictonary containing event info
        :param calendar_id: specific calendar id to mark the event with
        """

        temp = event.get('location', '').split(',')
        boxes = [box.split('-')[-1] for box in temp if 'Enheter' in box]
        creator_display_name = event.get('creator', {}).get('displayName', '')

        event_info = {
                'event_id': event['id'],
                'calendar_id': calendar_id,
                'timestamp_from': get_timestamp_from_event_time(event['start']),
                'timestamp_to': get_timestamp_from_event_time(event['end']),
                'event_summary': event.get('summary', ''),
                'event_button_names': boxes,
                'creator': creator_display_name
            }
        return event_info

    return Data(metadata=Metadata(timestamp=datetime.now().timestamp()), data=get_event_data())


def get_timestamp_from_event_time(start_or_end_time):
    """
    Converts a event time to a timestamp
    Format is specified in the google api docs. https://developers.google.com/calendar/v3/reference/events
    :param start_or_end_time: dictonary containing information a date or a dateTime for an event
    :return timestamp:
    """
    new_time_str = start_or_end_time.get('dateTime', start_or_end_time.get('date', None))
    if not new_time_str:
        raise KeyError

    return int(datetime.fromisoformat(new_time_str).timestamp())

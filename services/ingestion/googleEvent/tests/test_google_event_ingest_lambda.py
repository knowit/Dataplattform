from googleevent.google_event_ingest_lambda import handler
from pytest import fixture
from json import loads
from datetime import datetime
import copy
import pyrfc3339
from pytz import timezone as pytz_timezone
from freezegun import freeze_time
from time import sleep


@fixture
def with_frozen_time(datestring='2019-06-15 00:00:00', timezone_offset=+2):
    with freeze_time(datestring, tz_offset=timezone_offset):
        yield None


# Common start and end time for the test with mulitple calendars
# start_time_1/end_time_1 is for event in cal 1, and similar for cal 2
@fixture
def test_data(with_frozen_time):
    yield {
        'start_time_1': datetime(2019, 6, 15, 18, 30),
        'start_time_2': datetime(2019, 6, 16, 18, 30),
        'end_time_1': datetime(2019, 6, 15, 19, 30),
        'end_time_2': datetime(2019, 6, 16, 19, 30)
    }


@fixture(autouse=True)
def events_list_mock(mocker):
    mock_service_builder = mocker.patch('googleevent.google_event_ingest_lambda.googleapiclient.discovery.build')
    mocker.patch('googleevent.google_event_ingest_lambda.ServiceAccountCredentials')

    events_mock = mocker.MagicMock()
    mock_service_builder.return_value.events.return_value = events_mock

    events_mock.list = events_mock.list_next
    events_mock.list.return_value.execute.return_value = {}  # default
    yield events_mock.list


@fixture
def single_calendar_mock(mocker, events_list_mock):
    def payload(*data):
        def payload_generator():
            while True:  # Loop generated items
                for i, d in enumerate(data):
                    yield {**d,
                           **(
                                {'nextPageToken': 'test_page_token'} if i < len(data)-1
                                else {'nextSyncToken': 'test_sync_token'}
                           )}
        events_list_mock.return_value.execute = mocker.MagicMock(side_effect=payload_generator())

    yield payload


@fixture
def multi_calendar_mock(mocker, events_list_mock, test_data):
    def payload(generator):
        def list_side_effect(*args, **params):
            list_mock = mocker.MagicMock()
            list_mock.execute.return_value = {**generator(params['calendarId'], test_data),
                                              **{'calendarId': params['calendarId']}}
            return list_mock
        events_list_mock.side_effect = list_side_effect

    yield payload


def generate_cal_events(calendar_id, test_data):
    if (calendar_id == str(1)):
        start_time = test_data['start_time_1']
        end_time = test_data['end_time_1']
    elif (calendar_id == str(2)):
        start_time = test_data['start_time_2']
        end_time = test_data['end_time_2']
    else:
        assert False, 'Start and end times are not specified for calendar_id: ' + calendar_id

    test_events = {'items': [{
        'id': str(1234 + int(calendar_id)),
        'start': {
            'dateTime': start_time.isoformat()
                    },
        'end': {
            'dateTime': end_time.isoformat()
                },
        'location': 'Enheter-box' + calendar_id
        }]}
    return test_events


def test_events_multiple_calendars(s3_bucket, multi_calendar_mock, with_frozen_time, test_data):
    start_time_1 = test_data['start_time_1']
    start_time_2 = test_data['start_time_2']
    end_time_1 = test_data['end_time_1']
    end_time_2 = test_data['end_time_2']

    multi_calendar_mock(generate_cal_events)
    expected = [{'event_id': '1235',
                 'calendar_id': '1',
                 'timestamp_from': int(start_time_1.timestamp()),
                 'timestamp_to': int(end_time_1.timestamp()),
                 'event_summary': '',
                 'event_button_names': ['box1'],
                 'creator': ''
                 }]
    expected2 = [{'event_id': '1236',
                  'calendar_id': '2',
                  'timestamp_from': int(start_time_2.timestamp()),
                  'timestamp_to': int(end_time_2.timestamp()),
                  'event_summary': '',
                  'event_button_names': ['box2'],
                  'creator': ''
                  }]
    handler(None, None)

    expected_new = [expected[0], expected2[0]]
    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())
    assert [i for i in data['data'] if i not in expected_new] == []


def test_events_pagination(s3_bucket, single_calendar_mock, with_frozen_time, test_data):
    start_time_1 = test_data['start_time_1']
    end_time_1 = test_data['end_time_1']
    items1 = {
        'items': [{
            'id': '1234',
            'summary': 'test summary 1',
            'creator': {'displayName': 'Test Testerdaughter'},
            'start': {
                'dateTime': test_data['start_time_1'].isoformat()
            },
            'end': {
                'dateTime': test_data['end_time_1'].isoformat()
            },
            'location': 'Enheter-box1'
            }]}
    items2 = {
        'items': [{
            'id': '1235',
            'summary': 'test summary 2',
            'creator': {'displayName': 'Test Testerson'},
            'start': {
                'dateTime': start_time_1.isoformat()
            },
            'end': {
                'dateTime': end_time_1.isoformat()
            },
            'location': ''
            }]}

    single_calendar_mock(items1, items2)

    expected = [{'event_id': '1234',
                 'calendar_id': '1',
                 'timestamp_from': int(start_time_1.timestamp()),
                 'timestamp_to': int(end_time_1.timestamp()),
                 'event_summary': items1['items'][0]['summary'],
                 'event_button_names': ['box1'],
                 'creator': items1['items'][0]['creator']['displayName']
                 },
                {'event_id': '1235',
                 'calendar_id': '1',
                 'timestamp_from': int(start_time_1.timestamp()),
                 'timestamp_to': int(end_time_1.timestamp()),
                 'event_summary': items2['items'][0]['summary'],
                 'event_button_names': [],
                 'creator': items2['items'][0]['creator']['displayName']
                 }]
    expected2 = copy.deepcopy(expected)
    expected2[0]['calendar_id'] = '2'
    expected2[1]['calendar_id'] = '2'
    handler(None, None)
    expected_new = [expected[0], expected[1], expected2[0], expected2[1]]

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())
    assert [i for i in data['data'] if i not in expected_new] == []


def test_handler_time_format(s3_bucket, single_calendar_mock):
    test_date = datetime(2014, 4, 3).date()
    test_date2 = datetime(2014, 4, 4).date()
    test_date_str = test_date.isoformat()
    test_date2_str = test_date2.isoformat()

    single_calendar_mock({
        'items': [{
            'id': '1234',
            'start': {
                'date': test_date_str
            },
            'end': {
                'date': test_date2_str
            },
            'location': 'Enheter-box1'
        }]},
        {})

    handler(None, None)

    expected = [{'event_id': '1234',
                 'calendar_id': '1',
                 'timestamp_from': int(datetime(test_date.year, test_date.month, test_date.day).timestamp()),
                 'timestamp_to': int(datetime(test_date2.year, test_date2.month, test_date2.day).timestamp()),
                 'event_summary': '',
                 'event_button_names': ['box1'],
                 'creator': ''
                 },
                {'event_id': '1234',
                 'calendar_id': '2',
                 'timestamp_from': int(datetime(test_date.year, test_date.month, test_date.day).timestamp()),
                 'timestamp_to': int(datetime(test_date2.year, test_date2.month, test_date2.day).timestamp()),
                 'event_summary': '',
                 'event_button_names': ['box1'],
                 'creator': ''
                 }]

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())

    assert [i for i in data['data'] if i not in expected] == []


def test_handler_time_format_timezone(s3_bucket, single_calendar_mock, with_frozen_time):
    start_time_us = datetime(2019, 6, 15, 4, 0)  # GMT - 4
    us_time_zone = pytz_timezone('US/Eastern')
    oslo_time_zone = pytz_timezone('Europe/Oslo')
    start_time_us = us_time_zone.localize(start_time_us)
    start_time_us_rcf3339 = pyrfc3339.generate(start_time_us, utc=False)

    start_time_oslo = datetime(2019, 6, 15, 10, 0)

    end_time_oslo = datetime(2019, 6, 15, 13, 30)  # GM + 2
    end_time_oslo = oslo_time_zone.localize(end_time_oslo)
    end_time_1_rfc3339 = pyrfc3339.generate(end_time_oslo, utc=False)

    single_calendar_mock({
        'items': [{
            'id': '1234',
            'start': {
                'dateTime': start_time_us_rcf3339
            },
            'end': {
                'dateTime': end_time_1_rfc3339
            },
            'location': 'Enheter-box1'
        }]},
        {})

    handler(None, None)

    expected = [{'event_id': '1234',
                 'calendar_id': '1',
                 'timestamp_from': int(start_time_oslo.timestamp()),
                 'timestamp_to': int(end_time_oslo.timestamp()),
                 'event_summary': '',
                 'event_button_names': ['box1'],
                 'creator': ''
                 },
                {'event_id': '1234',
                 'calendar_id': '2',
                 'timestamp_from': int(start_time_oslo.timestamp()),
                 'timestamp_to': int(end_time_oslo.timestamp()),
                 'event_summary': '',
                 'event_button_names': ['box1'],
                 'creator': ''
                 }]

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())

    assert [i for i in data['data'] if i not in expected] == []


def test_handler_set_and_get_from_ssm(single_calendar_mock, ssm_client):
    single_calendar_mock({}, {})

    handler(None, None)

    last_sync_time_for_cal1 = ssm_client.get_parameter(Name='/dev/testService/last_poll_time_1',
                                                       WithDecryption=False)['Parameter']['Value']

    sleep(1)
    handler(None, None)

    new_sync_time_for_cal1 = ssm_client.get_parameter(Name='/dev/testService/last_poll_time_1',
                                                      WithDecryption=False)['Parameter']['Value']

    sync_time_is_updated = new_sync_time_for_cal1 != last_sync_time_for_cal1

    assert last_sync_time_for_cal1 is not None and sync_time_is_updated

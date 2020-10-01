from yr_process_lambda import handler
from dataplattform.common import schema
from pytest import fixture
from responses import RequestsMock, GET
from os import path
from json import load
import pandas as pd

location = 'Norway/Oslo/Oslo/Lakkegata'
url = f'https://www.yr.no/place/{location}/varsel_time_for_time.xml'


@fixture
def test_data2():
    with open(path.join(path.dirname(__file__), 'test_data2.json'), 'r') as json_file:
        yield load(json_file)


@fixture
def setup_queue_event(s3_bucket):
    def make_queue_event(data: schema.Data):
        s3_bucket.Object('/data/test.json').put(
            Body=data.to_json().encode('utf-8'))
        return {
            'Records': [{
                'body': '/data/test.json',
                'messageAttributes': {
                    's3FileName': {
                        'stringValue': '/data/test.json'
                    }
                }
            }]
        }
    yield make_queue_event


@fixture
def mocked_responses():
    with RequestsMock() as reqs:
        yield reqs


def test_hander_process_data(s3_bucket, mocked_responses, create_table_mock, setup_queue_event, test_data2):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data2['data']))

    handler(event, None)

    create_table_mock.assert_table_data_column(
        'yr_weather',
        'location',
        pd.Series(['Norway/Oslo/Oslo/Lakkegata']*24))

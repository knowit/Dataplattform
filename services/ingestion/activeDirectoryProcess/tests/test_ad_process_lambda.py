from pytest import fixture
from activedirectoryprocess.ad_process_lambda import handler
import pandas as pd
from io import BytesIO
from dataplattform.common import schema


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


def test_process(s3_bucket, setup_queue_event, dynamodb_resource):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data={}))
    handler(event, None)

    ad_data_parquet = s3_bucket.Object("data/test/structured/active_directory/part.0.parquet")
    ad_data = pd.read_parquet(BytesIO(ad_data_parquet.get()['Body'].read()))

    test_person_1 = ad_data.loc[ad_data['guid'] == "20dbbfa18380233aa643575720b893fac5137699"]
    test_person_2 = ad_data.loc[ad_data['guid'] == "491b9fa9bfac17563882b0fdc6f3a8a97417bd99"]
    test_person_3 = ad_data.loc[ad_data['guid'] == "5edbcdf460809039eb4897ccf8ce3bb5e501884d"]
    assert 'guid' in test_person_1.columns
    assert 'displayName' in test_person_1.columns
    assert 'email' in test_person_1.columns
    assert 'manager' in test_person_1.columns
    assert test_person_1.columns.size == 4
    assert test_person_1['displayName'][0] == "Per Nordmann"
    assert test_person_2['email'][1] == "kari.nordmann@knowit.no"
    assert test_person_3['manager'][2] == "Per Nordmann"

from io import BytesIO
from os import environ

import boto3
import functions.cache_updater as cache_updater
import pandas as pd
import pytest
from moto import mock_dynamodb2


@pytest.fixture
def db_data():
    yield [
        {
            "created": "2020-10-14T10:32:23.971390",
            "dataProtection": 3,
            "lastCacheUpdate": "2020-12-02T15:13:39.165031",
            "name": "testReport",
            "queryString": "COUNT(*) from dev_level_3_database.cv_partner_employees",
            "tables": [
                "test_table1",
                "test_table2"
            ]
        },
        {
            "created": "2020-10-14T10:32:23.971390",
            "dataProtection": 3,
            "lastCacheUpdate": "2020-12-02T15:13:39.165031",
            "name": "anotherReport",
            "queryString": "COUNT(*) from dev_level_3_database.cv_partner_employees",
            "tables": [
                "test_table3",
                "test_table4"
            ]
        }

    ]


@pytest.fixture
def dynamo_mock(db_data):
    with mock_dynamodb2():
        db = boto3.resource('dynamodb')
        table = db.create_table(
            AttributeDefinitions=[{'AttributeName': "name", 'AttributeType': 'S'}],
            TableName=f'{environ.get("STAGE", "dev")}_reports_table',
            KeySchema=[{'AttributeName': "name", 'KeyType': 'HASH'}],
            ProvisionedThroughput={'ReadCapacityUnits': 1, 'WriteCapacityUnits': 1}
        )
        for item in db_data:
            table.put_item(
                Item=item,
                Expected={
                    'name': {'Exists': False}
                }
            )
        yield table


@pytest.fixture
def test_event_data_update():
    yield {
        "Records": [
            {
                "Sns": {
                    "Message": '{"tables": ["test_table1"]}',
                    "Subject": "DataUpdate"
                }
            }]
    }


@pytest.fixture
def test_event_new_report():
    yield {
        "Records": [
            {
                "Sns": {
                    "Message": '{"report": "testReport"}',
                    "Subject": "NewReport"
                }
            }]
    }


def test_cache_updater_handler_data_update(s3_bucket, test_event_data_update, dynamo_mock):
    cache_updater.handler(test_event_data_update, None)
    res = BytesIO(s3_bucket.Object('reports/level-3/testReport.gzip').get()['Body'].read())
    result = pd.read_parquet(res, engine='fastparquet').to_csv()
    assert len(result) > 0 and 'col0' in result


def test_data_update_sets_last_data_update(test_event_data_update, dynamo_mock):
    cache_updater.handler(test_event_data_update, None)
    result = dynamo_mock.get_item(
        Key={'name': "testReport"}
    )
    assert result['Item']['lastCacheUpdate'] is not None


def test_cache_updater_handler_data_new(s3_bucket, test_event_new_report, dynamo_mock):
    cache_updater.handler(test_event_new_report, None)
    res = BytesIO(s3_bucket.Object('reports/level-3/testReport.gzip').get()['Body'].read())
    result = pd.read_parquet(res, engine='fastparquet').to_csv()
    assert len(result) > 0 and 'col0' in result


def test_new_report_sets_last_data_update(test_event_new_report, dynamo_mock):
    cache_updater.handler(test_event_new_report, None)
    result = dynamo_mock.get_item(
        Key={'name': "testReport"}
    )
    assert result['Item']['lastCacheUpdate'] is not None

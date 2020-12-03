from io import BytesIO

import functions.cache_updater as cache_updater
import pandas as pd
import pytest


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

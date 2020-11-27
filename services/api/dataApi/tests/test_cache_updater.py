import functions.cache_updater as cache_updater
import pandas as pd
import pytest


@pytest.fixture
def test_report():
    yield {
        "created": "2020-10-14T10:32:23.971390",
        "dataProtection": 3,
        "lastCacheUpdate": "2020-10-14T10:32:23.971390",
        "lastUsed": None,
        "name": "testReport",
        "queryString": "COUNT(*) from dev_level_3_database.cv_partner_employees",
        "tables": [
            "test_table"
        ]
    }


@pytest.fixture
def test_event_data_update():
    yield {
        "Records": [
            {
                "Sns": {
                    "Message": '{"tables": ["Hello from SNS!"]}',
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
                    "Message": '{"report": "test_name"}',
                    "Subject": "NewReport"
                }
            }]
    }


@pytest.fixture(autouse=True)
def reports_repo_mock(mocker, test_report):
    builder_get_by_tables = mocker.patch(
        "functions.cache_updater.ReportsRepository.get_by_tables"
    )
    builder_get = mocker.patch(
        "functions.cache_updater.ReportsRepository.get"
    )
    builder_get_by_tables.return_value = [test_report]
    builder_get.return_value = test_report
    mocker.patch(
        "functions.cache_updater.ReportsRepository.update_cache_time"
    )


def test_cache_updater_handler_data_update(s3_bucket, test_event_data_update):
    cache_updater.handler(test_event_data_update, None)
    s3_bucket.Object('reports/level-3/testReport.gzip').download_file('/tmp/testUpdateReport.gzip')
    result = pd.read_parquet('/tmp/testUpdateReport.gzip', engine='fastparquet').to_csv()
    assert len(result) > 0 and 'col0' in result


def test_cache_updater_handler_data_new(s3_bucket, test_event_new_report):
    cache_updater.handler(test_event_new_report, None)
    s3_bucket.Object('reports/level-3/testReport.gzip').download_file('/tmp/testUpdateReport.gzip')
    result = pd.read_parquet('/tmp/testUpdateReport.gzip', engine='fastparquet').to_csv()
    assert len(result) > 0 and 'col0' in result

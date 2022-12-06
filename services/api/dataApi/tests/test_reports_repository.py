from datetime import datetime
from unittest.mock import patch

import pytest
from common_lib.common.repositories.reports import ReportsRepository


def test_get(dynamo_mock):
    with ReportsRepository() as repo:
        get_result = repo.get("testReport")
    assert get_result['name'] == 'testReport'
    assert get_result['dataProtection'] == 3
    assert get_result['queryString'] == "COUNT(*) from dev_level_3_database.cv_partner_employees"


def test_get_by_one_table(dynamo_mock):
    with ReportsRepository() as repo:
        get_by_tables_result = repo.get_by_tables(["test_table1"])
    assert len(get_by_tables_result) == 1
    assert get_by_tables_result[0]["name"] == "testReport"


def test_get_by_many_tables(dynamo_mock):
    with ReportsRepository() as repo:
        get_by_tables_result = repo.get_by_tables(["test_table1", "test_table2"])
    assert len(get_by_tables_result) == 1
    assert get_by_tables_result[0]["name"] == "testReport"


def test_all(dynamo_mock):
    with ReportsRepository() as repo:
        all_result = repo.all()
    assert len(all_result) == 2
    assert all_result[0]["name"] == "testReport"
    assert all_result[1]["name"] == "anotherReport"


def test_create(dynamo_mock):
    additional_report = {
        "dataProtection": 3,
        "name": "new_report",
        "queryString": "COUNT(*) from dev_level_3_database.cv_partner_employees",
        "tables": [
            "test_table5",
            "test_table6"
        ],
        "lastUsed": "fail",
        "lastCacheUpdate": "fail"
    }
    with ReportsRepository() as repo:
        repo.create(additional_report)
    new_item_result = dynamo_mock.get_item(Key={"name": "new_report"})
    assert new_item_result['Item']['name'] == "new_report"
    assert new_item_result['Item']['created'] is not None


def test_update_cache_time(dynamo_mock):
    with patch("common_lib.common.repositories.reports.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2020, 1, 1)
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        with ReportsRepository() as repo:
            repo.update_cache_time("testReport")
        new_item_result = dynamo_mock.get_item(Key={"name": "testReport"})
        assert new_item_result['Item']['lastCacheUpdate'] == datetime(2020, 1, 1).isoformat()


def test_update_cache_time_non_existing(dynamo_mock):
    with patch("common_lib.common.repositories.reports.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2020, 1, 1)
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        with ReportsRepository() as repo:
            with pytest.raises(KeyError):
                repo.update_cache_time("testReport_non_existing")


def test_delete(dynamo_mock):
    with ReportsRepository() as repo:
        repo.delete("testReport")
    all_reports = dynamo_mock.scan()
    assert len(all_reports['Items']) == 1
    assert all_reports['Items'][0]['name'] == "anotherReport"

import json
from io import BytesIO

import pytest
import pandas as pd
from functions.cache_deleter import handler


cache_path = "reports/level-3/testReport.gzip"


@pytest.fixture
def mock_report_cache():
    dataframe = pd.DataFrame({'a': [1, 1, 1], 'b': [1, 2, 3]})

    file = BytesIO()

    dataframe.to_parquet(
        file,
        compression='GZIP',
        index=False
    )
    yield file


@pytest.fixture
def s3_with_report(s3_bucket, mock_report_cache):
    s3_bucket.put_object(
        Key=cache_path,
        Body=mock_report_cache)
    yield s3_bucket


@pytest.fixture
def sns_message():
    yield {
        'Records': [
            {
                'Sns': {
                    'Subject': 'DeleteReport',
                    'Message': json.dumps({
                        'name': 'testReport',
                        'dataProtection': 3
                    })
                }
            }
        ]
    }


def test_delete(s3_with_report, sns_message):
    handler(sns_message, None)
    all_objects = s3_with_report.objects.all()
    assert all([obj.key != cache_path for obj in all_objects])

import boto3
import os
from pathlib import Path
import json


def mock(event, context):
    try:
        mock_file_path = (
            Path(__file__).resolve().parent.parent.parent / Path('tests/test_data') / Path('test_data_mock.json')
            )
        with open(mock_file_path) as f:
            mock_json = json.load(f)

        dynamodb = boto3.resource('dynamodb')
        table_name = os.environ['STAGE'] + '_personal_metadata_table'
        table = dynamodb.Table(table_name)

        with table.batch_writer() as batch:
            for ad_user in mock_json:
                batch.put_item(
                    Item={
                        'guid': ad_user['guid'],
                        'alias': ad_user['alias'],
                        'company': ad_user['company'],
                        'displayName': ad_user['displayName'],
                        'distinguished_name': ad_user['distinguished_name'],
                        'email': ad_user['email'],
                        'knowitBranch': ad_user['knowitBranch'],
                        'manager': ad_user['manager'],
                        'manager_email': ad_user['manager_email']
                    }
                )

        return dict(
            statusCode=200
        )
    except Exception as e:
        return dict(
            statusCode=500,
            body=str(e)
        )

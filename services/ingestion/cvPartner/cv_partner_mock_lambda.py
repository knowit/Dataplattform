import json
from dataplattform.common.handlers.ingest import IngestHandler
from dataplattform.common.schema import Data, Metadata
from dataplattform.common.helper import empty_content_in_path
import boto3
from os import environ, scandir

handler = IngestHandler()


@handler.ingest(overwrite=True)
def mock(event) -> Data:
    aws_client = boto3.client('s3')

    empty_content_in_path(bucket=environ.get('PRIVATE_BUCKET'), prefix=environ.get('PRIVATE_PREFIX'))
    empty_content_in_path(bucket=environ.get('PUBLIC_BUCKET'), prefix=environ.get('PUBLIC_PREFIX'))

    data = open('tests/test_data/test_data.json')
    data_json = json.load(data)

    for entry in scandir('tests/test_data/test_files'):
        bucket = environ.get('PUBLIC_BUCKET') if entry.path.endswith('.jpg') else environ.get('PRIVATE_BUCKET')
        aws_client.upload_file(entry.path, bucket, entry.name)

    return Data(
        metadata=Metadata(timestamp=data_json['metadata']['timestamp']),
        data=data_json['data']
    )
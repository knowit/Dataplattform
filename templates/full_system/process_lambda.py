from dataplattform.common.handler import Handler
from dataplattform.common.schema import Data, Metadata
from dataplattform.common.aws import S3
from datetime import datetime
import pandas as pd
from typing import Dict
import boto3
from os import environ

handler = Handler()


@handler.ingest()
def ingest(event) -> Data:
    return Data(
        metadata=Metadata(timestamp=int(datetime.now().timestamp())),
        data=event["Records"])

@handler.process(partitions={})
def process(data) -> Dict[str, pd.DataFrame]:
    print('---------------------- In process lambda ----------------------\n')
    print(data[0])

    def get_s3_key(d):
        d = d.json()
        return d['data'][0]['messageAttributes']['s3FileName']

    s3_keys = [get_s3_key(d) for d in data]
    print(s3_keys)

    # fetch files from s3
    # do processing on files

    return {'some_structured_data': pd.DataFrame()}

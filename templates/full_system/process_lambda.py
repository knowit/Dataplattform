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
def ingest(event):
    return None


@handler.process(partitions={})
def process(data) -> Dict[str, pd.DataFrame]:
    print('---------------------- In process lambda ----------------------\n')
    print(event)
    
    filename = 'raw/' + event['Records'][0]['body'] + '.json'
    s3 = S3(environ['ACCESS_PATH'])
    print(environ['ACCESS_PATH'])

    test_text = s3.get(filename).json()
    print(test_text)
    data = test_text

    def make_dataframe(d, timestamp):
        df = pd.json_normalize(d)
        df['time'] = int(timestamp)
        return df

    return pd.concat([make_dataframe(d, data['metadata']['timestamp']) for d in data['data']])

from dataplattform.common.process_handler import Handler
from dataplattform.common.schema import Data, Metadata
from dataplattform.common.aws import S3
from datetime import datetime
import pandas as pd
from typing import Dict
import boto3
from os import environ

handler = Handler()


@handler.process(partitions={})
def process(data) -> Dict[str, pd.DataFrame]:
    print(data)

    def make_dataframe(d):
        d = d.json()
        metadata, payload = d['metadata'], d['data']
        df = pd.json_normalize(payload)
        df['time'] = int(metadata['timestamp'])
        return df

    out_df = pd.concat([make_dataframe(d) for d in data])
    return {'some_structured_data': out_df}

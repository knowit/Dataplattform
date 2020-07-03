from dataplattform.common.process_handler import Handler
from dataplattform.common.schema import Data, Metadata
from dataplattform.common.aws import S3
from datetime import datetime
import pandas as pd
from typing import Dict
import boto3
from os import environ
from time import sleep
from random import randint

handler = Handler()


@handler.process(partitions={})
def process(data) -> Dict[str, pd.DataFrame]:
    def make_dataframe(d, sent, rec):
        d = d.json()
        metadata, payload = d['metadata'], d['data']
        df = pd.json_normalize(payload)
        df['time'] = int(metadata['timestamp'])
        df['time_sent'] = sent
        df['time_recieved'] = rec
        return df

    out_df = pd.concat([make_dataframe(d1, sent, rec) for d1, sent, rec in zip(data[0], data[1], data[2])])
    return {'some_structured_data': out_df}

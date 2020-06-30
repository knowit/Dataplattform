from dataplattform.common.ingest_handler import Handler
from dataplattform.common.schema import Data, Metadata
from datetime import datetime
import pandas as pd
from typing import Dict
import boto3
from os import environ
import json

handler = Handler()


@handler.ingest()
def ingest(event) -> Data:

    timestamp_now = int(datetime.now().timestamp())
    d = [{'test': 'This is a test message', 'id': 1}, {'test': 'This is also a test message', 'id': 2}]
    return Data(
        metadata=Metadata(timestamp=int(timestamp_now)),
        data=d)

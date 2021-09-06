from dataplattform.common.handler import Handler
from dataplattform.common.schema import Data, Metadata
from dataplattform.common.aws import SSM
from datetime import datetime
import pandas as pd
import requests
from typing import Dict
from dateutil.parser import isoparse

handler = Handler()
url = 'https://api.github.com/repos/knowit/Dataplattform/events'


@handler.ingest()
def ingest(event) -> Data:
    api_token = SSM(with_decryption=True).get('github_api_token')
    res = requests.get(url, headers={'Authorization': f'Bearer {api_token}'})
    events = res.json()

    def to_timestamp(date):
        return int(isoparse(date).timestamp()) if isinstance(date, str) else int(date)

    def data_point(event):
        return {
            'id': event['id'],
            'type': event['type'],
            'merged_at': to_timestamp(event['payload']['pull_request']['merged_at']),
            'created_at': to_timestamp(event['payload']['pull_request']['created_at']),
            'base-ref': event['base']['ref']
        }

    return Data(metadata=Metadata(timestamp=datetime.now().timestamp()), data=[data_point(event) for event in events])


@handler.process(partitions={})
def process(data) -> Dict[str, pd.DataFrame]:
    return {}

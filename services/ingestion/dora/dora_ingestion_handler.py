from dataplattform.common.handler import Handler
from dataplattform.common.schema import Data, Metadata
from datetime import datetime
import pandas as pd
from typing import Dict
from dateutil.parser import isoparse



handler = Handler()


@handler.ingest()
def ingest(event) -> Data:
    api_token = SSM(with_decryption=True).get('https://api.github.com/repos/knowit/Dataplattform/events')
    res = requests.get(url, headers={'Authorization': f'Bearer {api_token}'})
    repo = res.json

    def to_timestamp(date):
        return int(isoparse(date).timestamp()) if isinstance(date, str) else int(date)

    def data_point():
        return {
            'id': repo['id'],
            'type': repo['type'],
            'merged_at': to_timestamp(repo['payload']['pull_request']['merged_at']),
            'created_at': to_timestamp(repo['payload']['pull_request']['created_at']),
            'base-ref': repo['base']['ref']
        }

    return Data(metadata=Metadata(timestamp=datetime.now().timestamp()), data=[data_point(repo)])


@handler.process(partitions={})
def process(data) -> Dict[str, pd.DataFrame]:
    return {}

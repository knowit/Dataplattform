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
            'name': repo['name'],
            'description': repo['description'],
            'url': repo['url'],
            'html_url': repo['html_url'],
            'owner': repo['owner']['login'],
            'created_at': to_timestamp(repo['created_at']),
            'updated_at': to_timestamp(repo['updated_at']),
            'pushed_at': to_timestamp(repo['pushed_at']),
            'language': repo['language'],
            'forks_count': repo['forks_count'],
            'stargazers_count': repo['stargazers_count'],
            'default_branch': repo['default_branch']
        }

    return Data(metadata=Metadata(timestamp=datetime.now().timestamp()), data=[data_point(repo)])


@handler.process(partitions={})
def process(data) -> Dict[str, pd.DataFrame]:
    return {}

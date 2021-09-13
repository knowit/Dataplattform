from dataplattform.common.handlers.process import ProcessHandler
import pandas as pd
from typing import Dict

handler = ProcessHandler()


@handler.process(partitions={'github_dora_repos': ['name']})
def process(data, events) -> Dict[str, pd.DataFrame]:
    def make_dataframe(d):
        d = d.json()
        metadata, payload = d['metadata'], d['data']
        repos_dataframe = pd.json_normalize(payload)
        repos_dataframe['time'] = int(metadata['timestamp'])
        return repos_dataframe

    dora_data = [
        'name',
        'id',
        'type',
        'merged_at',
        'created_at',
        'base-ref'
    ]
    github_dataframe = pd.concat([make_dataframe(d) for d in data])
    dora_datas = github_dataframe.loc[:, dora_data]

    return {'github_dora_repos': dora_datas}

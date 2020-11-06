from dataplattform.common.handlers.process import ProcessHandler
from typing import Dict
import pandas as pd


handler = ProcessHandler()


@handler.process(partitions={}, overwrite=True)
def process(data, events) -> Dict[str, pd.DataFrame]:
    def make_dataframe(d):
        d = d.json()
        metadata, payload = d['metadata'], d['data']
        df = pd.json_normalize(payload)
        df['time'] = int(metadata['timestamp'])
        return df

    df_new = pd.concat([make_dataframe(d) for d in data])
    return {
        'activeDirectory': df_new
    }

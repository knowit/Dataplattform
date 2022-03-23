from dataplattform.common.handlers.process import ProcessHandler
import pandas as pd
from typing import Dict


handler = ProcessHandler()


@handler.process(partitions={'yr_weather': ['location_name']})
def process(data, events) -> Dict[str, pd.DataFrame]:

    def make_dataframe(d):
        d = d.json()
        metadata, payload = d['metadata'], d['data']
        df = pd.json_normalize(payload)
        df['time'] = int(metadata['timestamp'])
        return df

    df = pd.concat([make_dataframe(d) for d in data])

    # TODO: Check for duplicates?
    return {
        'yr_weather': df
    }

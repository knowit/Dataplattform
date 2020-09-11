from dataplattform.common.handler import Handler

import pandas as pd
from typing import Dict

handler = Handler()


@handler.process(partitions={})
def process(data) -> Dict[str, pd.DataFrame]:
    def make_dataframe(d):
        d = d.json()
        metadata, payload = d['metadata'], d['data']
        df = pd.json_normalize(payload)
        df['time'] = int(metadata['timestamp'])
        return df

    df_new = pd.concat([make_dataframe(d) for d in data])
    return {
        'google_calendar_events': df_new
    }

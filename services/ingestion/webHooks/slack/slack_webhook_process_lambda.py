from dataplattform.common.handlers.process import ProcessHandler
from typing import Dict
import pandas as pd
import numpy as np


handler = ProcessHandler()


@handler.process(partitions={'slack_emoji': ['event_type']})
def process(data, events) -> Dict[str, pd.DataFrame]:
    data = [
        [dict(x, time=d['metadata']['timestamp']) for x in d['data']]
        for d in [d.json() for d in data]
    ]
    data = np.hstack(data)
    df = pd.DataFrame.from_records(data)

    return {
        'slack_emoji': df,
    }

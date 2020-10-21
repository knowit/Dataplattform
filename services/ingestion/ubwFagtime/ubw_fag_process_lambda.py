from dataplattform.common.handlers.process import ProcessHandler
from dataplattform.query.engine import Athena
from typing import Dict
import pandas as pd
import numpy as np


handler = ProcessHandler()
ath = Athena()


@handler.process(partitions={})
def process(data, events) -> Dict[str, pd.DataFrame]:
    data = [
        [dict(x, time=d['metadata']['timestamp']) for x in d['data']]
        for d in [d.json() for d in data]
    ]

    data = np.hstack(data)
    df = pd.DataFrame.from_records(data)

    # Get unique reg_periods where used_hrs are largest
    df = df[['time', 'reg_period', 'used_hrs']].sort_values(['used_hrs']).groupby('reg_period').first().reset_index()

    reg_period_df = ath.from_('ubw_fagtimer').select('reg_period').execute(ath).as_pandas()
    df = df[~df.reg_period.isin(reg_period_df.reg_period)]

    return {
        'ubw_fagtimer': df
    }

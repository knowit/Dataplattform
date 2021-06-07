from dataplattform.common.handlers.process import ProcessHandler
import pandas as pd
from typing import Dict


handler = ProcessHandler()


@handler.process(partitions={}, overwrite=True, overwrite_all_versions=True)
def process(data, events) -> Dict[str, pd.DataFrame]:
    out_df = pd.concat([pd.json_normalize(d.json()['data'])for d in data])
    return {'person_data_test_6': out_df}

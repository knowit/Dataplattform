from dataplattform.common.handlers.process import ProcessHandler
import pandas as pd
from typing import Dict


handler = ProcessHandler()


@handler.process(partitions={})
def process(data, events) -> Dict[str, pd.DataFrame]:
    out_df = pd.concat([pd.json_normalize(d.json()['data'])for d in data])
    return {'some_structured_data': out_df}

from dataplattform.common.handler import Handler
from dataplattform.common.schema import Data, Metadata
from datetime import datetime
import pandas as pd
from typing import Dict


handler = Handler()


@handler.ingest()
def ingest(event) -> Data:
    return Data(
        metadata=Metadata(timestamp=datetime.now().timestamp()),
        data=None)


@handler.process(partitions={})
def process(data) -> Dict[str, pd.DataFrame]:
    return {}

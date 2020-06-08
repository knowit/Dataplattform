from dataplattform.common.handler import Handler
from dataplattform.common.schema import Data, Metadata
from datetime import datetime
from typing import Dict, AnyStr
from dataclasses import dataclass
from dateutil.parser import isoparse
import pandas as pd


handler = Handler()



@handler.ingest()
def ingest(event) -> Data:

    @dataclass
    class GoogleFormsMetaData(Metadata):
        event: AnyStr

    # TODO: find time format 
    def to_timestamp(date):
        return int(isoparse(date).timestamp()) if isinstance(date, str) else int(date)

    return Data(
        metadata=GoogleFormsMetaData(
            timestamp=datetime.now().timestamp(),
            event={}),
        data=event['body']
    )


@handler.process(partitions={})
def process(data) -> Dict[str, pd.DataFrame]:
    # records = [dict(x['data'], time=int(x['metadata']['timestamp'])) for x in [d.json() for d in data]]
    return {
       #  'custom_table_name': pd.DataFrame.from_records(records)
    }
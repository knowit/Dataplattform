from dataplattform.common.handler import Handler
from dataplattform.common.schema import Data, Metadata
from dataplattform.common.aws import SSM
from datetime import datetime
from json import loads
from typing import Dict, AnyStr
import pandas as pd
from dataclasses import dataclass
from itertools import groupby
from dateutil.parser import isoparse


handler = Handler()



@handler.ingest()
def ingest(event) -> Data:
    body = loads(event['body'])
    event_type, item = body['webhookEvent'].split(':')[-1], body['issue']

    @dataclass
    class GoogleFormsMetadata(Metadata):
        event_type: AnyStr

    return Data(
        metadata=GoogleFormsMetadata(
            timestamp=datetime.now().timestamp(),
            event_type=event_type
        ),
        data={
        }
    )

@handler.process(partitions={})
def process(data) -> Dict[str, pd.DataFrame]:
    records = [dict(x['data'], time=int(x['metadata']['timestamp'])) for x in [d.json() for d in data]]
    return {
        'custom_table_name': pd.DataFrame.from_records(records)
    }

    return {}

from dataplattform.common.handler import Handler
from dataplattform.common.schema import Data, Metadata
from datetime import datetime
import pandas as pd
import json
from typing import Dict

handler = Handler()

@handler.ingest()
def ingest(event) -> Data:

    print("type", type(event['body']))
    print("value", event['body'])

    return Data(
        Metadata(timestamp=int(datetime.now().timestamp())),
        data=json.loads(event['body'])
    )


@handler.process(partitions={})
def process(data) -> Dict[str, pd.DataFrame]:
    def make_dataframes(d):
        d = d.json()
        metadata, payload = d['metadata'], d['data']
        print("payload: ", payload)
        table_name = payload['tableName']
        table_content = payload['values']
        data_df = pd.DataFrame(table_content[1:], columns=table_content[0])
        table_name = table_name.replace(" ", "_")  # TODO: other not allowed chars?
        data_df = pd.json_normalize(payload)
        
        metadata_df = pd.DataFrame({'author': [payload['email']], 'timestamp': [metadata['timestamp']]})
        return table_name, metadata_df, data_df

    table_name, metadata_df, data_df = make_dataframes(data[0])

    return {
            table_name: data_df,
            'google_sheets_metadata': metadata_df
    }

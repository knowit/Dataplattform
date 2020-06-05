from dataplattform.common.handler import Handler
from dataplattform.common.schema import Data, Metadata
from datetime import datetime
import pandas as pd
import json
from typing import Dict

handler = Handler()


@handler.ingest()
def ingest(event) -> Data:

    return Data(
        Metadata(timestamp=int(datetime.now().timestamp())),
        data=json.loads(event.get('body', "{}"))
    )


@handler.process(partitions={})
def process(data) -> Dict[str, pd.DataFrame]:
    def make_dataframes(d):
        d = d.json()
        metadata, payload = d['metadata'], d['data']
        timestamp = metadata['timestamp']
        table_name = payload.get('tableName', 'untitled' + str(timestamp))  # TODO: Add warning?
        table_content = payload.get('values', None)
        data_df = pd.DataFrame()

        if table_content:
            data_df = pd.DataFrame(table_content[1:], columns=table_content[0])
            table_name = table_name.replace(" ", "_")  # TODO: other not allowed chars?

        metadata_df = pd.DataFrame({'author': [payload.get('email', 'undefined')],
                                    'time_added_to_dataplattform': [metadata['timestamp']],
                                    'inserted_tables': [table_name]})
        return table_name, metadata_df, data_df

    table_name, metadata_df, data_df = make_dataframes(data[0])

    return {
            table_name: data_df,
            'google_sheets_metadata': metadata_df
    }

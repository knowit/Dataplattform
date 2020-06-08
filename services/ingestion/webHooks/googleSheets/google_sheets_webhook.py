from dataplattform.common.handler import Handler
from dataplattform.common.schema import Data, Metadata
from datetime import datetime
import pandas as pd
import json
import numpy as np
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
        table_name = payload['tableName']
        table = payload.get('values', None)
        data_df = pd.DataFrame()
        if table:
            tmp_array = np.array(table, dtype=np.object_)
            mask = tmp_array == ''
            rows = np.flatnonzero((~mask).sum(axis=1))
            cols = np.flatnonzero((~mask).sum(axis=0))
            cropped_table = tmp_array[rows.min():rows.max()+1, cols.min():cols.max()+1]
            content = cropped_table[1:, :]
            column_names = cropped_table[0, :]
            data_df = pd.DataFrame(content.tolist(), columns=column_names.tolist(), dtype=None)

        metadata_df = pd.DataFrame({'author': [payload.get('user', 'undefined')],
                                    'time_added_to_dataplattform': [metadata['timestamp']],
                                    'inserted_tables': [table_name]})
        return table_name, metadata_df, data_df

    table_name, metadata_df, data_df = make_dataframes(data[0])

    return {
            table_name: data_df,
            'google_sheets_metadata': metadata_df
    }

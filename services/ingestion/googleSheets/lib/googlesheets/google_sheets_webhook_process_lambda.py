from dataplattform.common.handlers.process import ProcessHandler
import pandas as pd
import numpy as np
from typing import Dict
import re

handler = ProcessHandler()


@handler.process(partitions={}, overwrite=True)
def process(data, events) -> Dict[str, pd.DataFrame]:

    def make_dataframes(d):
        d = d.json()
        metadata, payload = d['metadata'], d['data']
        user = payload.get('user', 'undefined')

        table_name = payload['tableName']
        table_name = user + '-' + table_name  # avoid overwrite
        table_name = re.sub('[^A-Za-z0-9]+', '_', table_name)

        table = payload.get('values', None)

        data_df = pd.DataFrame()
        if table:
            tmp_array = np.array(table, dtype=np.object_)
            mask = tmp_array == ''
            rows = np.flatnonzero((~mask).sum(axis=1))
            cols = np.flatnonzero((~mask).sum(axis=0))
            cropped_table = tmp_array[rows.min(
            ):rows.max()+1, cols.min():cols.max()+1]
            content = cropped_table[1:, :]
            column_names = cropped_table[0, :]
            data_df = pd.DataFrame(
                content.tolist(), columns=column_names.tolist(), dtype=None)
            # Replace " " with nullable
            data_df = data_df.replace(r'^\s*$', pd.NA, regex=True)

        metadata_df = pd.DataFrame({'uploaded_by_user': user,
                                    'time_added': [metadata['timestamp']],
                                    'inserted_tables': [table_name]})
        return table_name, data_df, metadata_df

    data_tables, metadata_tables = list(zip(*[
        (
            (table_name, data_df),
            metadata_df
        ) for table_name, data_df, metadata_df in [make_dataframes(d) for d in data]
    ]))

    return {
        **dict(data_tables),
        'google_sheets_metadata': pd.concat(metadata_tables)
    }

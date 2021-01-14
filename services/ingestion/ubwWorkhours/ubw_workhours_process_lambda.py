from dataplattform.common.handlers.process import ProcessHandler
from typing import Dict
import pandas as pd
import numpy as np


handler = ProcessHandler()


@handler.process(partitions={'ubw_costumer_per_resource': ['time']})
def process(data, events) -> Dict[str, pd.DataFrame]:
    data = [
        [dict(x, time=d['metadata']['timestamp']) for x in d['data']]
        for d in [d.json() for d in data]
    ]

    def column_type_to_float(col):
        col = pd.to_numeric(col, errors='coerce')
        col = col.fillna(value=0)
        col = col.astype(dtype='float32')
        return col

    data = np.hstack(data)

    df = pd.DataFrame.from_records(data)

    col_selection_table = [
        "reg_period",
        "used_hrs",
        "resource_id",
        "xresource_id",
        "xr1project",
        "work_order",
        "xwork_order",
        "xr0work_order",
        "time"
    ]
    work_hours_df = df[col_selection_table].copy()
    work_hours_df.rename(columns={
        'resource_id': 'resource_alias',
        'xresource_id': 'resource_name',
        'xwork_order': 'work_order_description',
        'xr1project': 'project_type',
        'xr0work_order': 'costumer'}, inplace=True)

    work_hours_df['used_hrs'] = column_type_to_float(work_hours_df['used_hrs'])
    work_hours_df = work_hours_df.dropna().copy()
    work_hours_df = work_hours_df.loc[lambda work_hours_df: work_hours_df['used_hrs'] > 0]

    # Find all unique aliases
    unique_aliases = work_hours_df.resource_alias.unique()

    df_list = []
    for alias in unique_aliases:
        tmp_df = work_hours_df.loc[work_hours_df['resource_alias'] == alias].copy()
        tmp_df = tmp_df.sort_values(by=['used_hrs'], ascending=False).copy()
        tmp_df['weigth'] = np.arange(1, len(tmp_df['used_hrs'])+1, 1)
        df_list.append(tmp_df)

    df = pd.concat(df_list, ignore_index=True)

    return {
        'ubw_costumer_per_resource': df
    }

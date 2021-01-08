from dataplattform.common.handlers.process import ProcessHandler
from typing import Dict
import pandas as pd
import numpy as np


handler = ProcessHandler()


@handler.process(partitions={})
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
        "f0_billable",
        "resource_id",
        "xresource_id",
        "xr1project",
        "work_order",
        "xwork_order",
        "xr0work_order"
    ]
    work_hours_df = df[col_selection_table].copy()
    work_hours_df.rename(columns={
        'f0_billable': 'billable',
        'resource_id': 'resource_alias',
        'xresource_id': 'resource_name',
        'xr1project': 'project_type',
        'xwork_order': 'work_order_description',
        'xr0work_order': 'costumer'}, inplace=True)

    work_hours_df['used_hrs'] = column_type_to_float(work_hours_df['used_hrs'])
    work_hours_df = work_hours_df.loc[lambda work_hours_df: work_hours_df['used_hrs'] > 0]

    return {
        'ubw_workhours': work_hours_df
    }

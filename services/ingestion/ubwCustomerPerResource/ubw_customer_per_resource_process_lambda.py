import os

from dataplattform.common.aws import S3
from dataplattform.common.handlers.process import PersonDataProcessHandler
from dataplattform.common.repositories.person_repository import PersonIdentifierType
from typing import Dict
from datetime import datetime
from os import environ
import pandas as pd
import numpy as np

handler = PersonDataProcessHandler(PersonIdentifierType.ALIAS)


@handler.process(partitions={}, overwrite=True, overwrite_all_versions=True,
                 person_data_tables=['ubw_customer_per_resource'],
                 historical_tables=['ubw_per_project_data'])
def process(data, events) -> Dict[str, pd.DataFrame]:
    data = [
        [dict(x, time=int(d['metadata']['timestamp'])) for x in d['data']]
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
        "xr1project",
        "work_order",
        "xwork_order",
        "xr0work_order",
        "time"
    ]
    work_hours_df = df[col_selection_table].copy()
    work_hours_df.rename(columns={
        'resource_id': 'alias',
        'xwork_order': 'work_order_description',
        'xr1project': 'project_type',
        'xr0work_order': 'customer'}, inplace=True)

    work_hours_df['used_hrs'] = column_type_to_float(work_hours_df['used_hrs'])
    work_hours_df['alias'] = work_hours_df['alias'].str.lower()
    work_hours_df = work_hours_df.dropna().copy()
    work_hours_df = work_hours_df.loc[lambda work_hours_df: work_hours_df['used_hrs'] > 0]

    # Find all unique aliases
    unique_aliases = work_hours_df.alias.unique()
    df_list = []
    for alias in unique_aliases:
        tmp_df = work_hours_df.loc[work_hours_df['alias'] == alias].copy()
        tmp_df = tmp_df.sort_values(by=['used_hrs'], ascending=False).copy()
        tmp_df['weigth'] = np.arange(1, len(tmp_df['used_hrs']) + 1, 1)
        df_list.append(tmp_df)

    df = pd.concat(df_list, ignore_index=True)

    def get_per_project_data(dataframe):
        project_customers = []
        reg_period = dataframe.iloc[0]['reg_period']
        timestamp = dataframe.iloc[0]['time']
        for customer in dataframe['customer'].unique():
            project_customers.append({
                'customer': customer,
                'employees': dataframe[dataframe['customer'] == customer]['alias'].unique().shape[0],
                'hours': dataframe[dataframe['customer'] == customer]['used_hrs'].sum(),
                'reg_period': reg_period,
                'timestamp': timestamp
            })
        return pd.DataFrame(project_customers)

    per_project_data = get_per_project_data(df)
    df.pop('used_hrs')

    s3 = S3()
    if s3.fs.exists('structured/ubw_customer_per_resource/part.0.parquet'):
        s3_path = os.path.join('s3://',
                               environ.get('DATALAKE'),
                               environ.get('ACCESS_PATH'),
                               'structured/ubw_customer_per_resource')
        old_frame = pd.read_parquet(s3_path)

        cur_year, cur_week = datetime.now().isocalendar()[0:2]
        cur_weeks = cur_year * 52 + cur_week

        def filter_by_week(row):
            weeks = int(row['reg_period'][0:4]) * 52 + int(row['reg_period'][4:])
            return weeks > cur_weeks - 4

        old_frame = old_frame[old_frame.apply(filter_by_week, axis=1)]
        df = pd.concat([df, old_frame]).drop(columns=['guid']).drop_duplicates(subset=df.columns.difference(['time']))

    return {
        'ubw_customer_per_resource': df,
        'ubw_per_project_data': per_project_data
    }

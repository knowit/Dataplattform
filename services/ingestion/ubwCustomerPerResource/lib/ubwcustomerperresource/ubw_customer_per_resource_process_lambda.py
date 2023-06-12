from dataplattform.common.aws import S3
from dataplattform.common.handlers.process import PersonDataProcessHandler
from dataplattform.common.repositories.person_repository import PersonIdentifierType
from typing import Dict
import os
import pandas as pd
import numpy as np
from pathlib import PurePosixPath

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
        timestamp = dataframe.iloc[0]['time']
        new_dataframe = dataframe.drop_duplicates(
            subset=["customer", "work_order_description", "reg_period"], keep="last")
        df_with_employees = dataframe.drop_duplicates(
            subset=["customer", "work_order_description", "alias"],
            keep="last"
        ).groupby(
            ['customer', 'work_order_description']).size().reset_index(name="employees")
        for (index, row) in new_dataframe.iterrows():
            project_customers.append({
                'customer': row["customer"],
                'employees': df_with_employees[
                    (df_with_employees["customer"] == row["customer"])
                    & (df_with_employees["work_order_description"] == row["work_order_description"])
                ]["employees"].sum(),
                'hours': dataframe[
                    (dataframe['customer'] == row["customer"])
                    & (dataframe['work_order_description'] == row["work_order_description"])
                    & (dataframe['reg_period'] == row["reg_period"])
                ]['used_hrs'].sum(),
                'reg_period': row["reg_period"],
                'timestamp': timestamp,
                'work_order': row["work_order_description"]
            })

        
        return pd.DataFrame(project_customers)
    
    def get_per_customer_data(dataframe):
        project_customers = []
        timestamp = dataframe.iloc[0]['time']
        new_dataframe = dataframe.drop_duplicates(
            subset=["customer", "work_order_description", "reg_period"], keep="last")
        df_without_workorders = dataframe.drop_duplicates(
            subset=["customer", "work_order_description", "alias"],
            keep="last"
        ).groupby(
            ['customer']).size().reset_index(name="employees")
        for (index, row) in new_dataframe.iterrows():
            project_customers.append({
                'customer': row["customer"],
                'employees': df_without_workorders[
                    (df_without_workorders["customer"] == row["customer"])
                ]["employees"].sum(),
                
                'hours': dataframe[
                    (dataframe['customer'] == row["customer"])
                    & (dataframe['reg_period'] == row["reg_period"])
                ]['used_hrs'].sum(),
                'reg_period': row["reg_period"],
                'timestamp': timestamp
            })
        return pd.DataFrame(project_customers)

    per_project_data = get_per_project_data(df)
    per_customer_data = get_per_customer_data(df)
    df.pop('used_hrs')

    s3 = S3()
    if s3.fs.exists('structured/ubw_customer_per_resource/part.0.parquet'):
        s3_path = PurePosixPath(os.environ.get('DATALAKE'),
                                os.environ.get('ACCESS_PATH'),
                                'structured/ubw_customer_per_resource')
        old_frame = pd.read_parquet(f's3://{s3_path}')

        num_weeks = int(os.environ.get('NUM_WEEKS', '4'))

        updated_reg_periods = old_frame['reg_period'].astype('str')
        reg_periods = old_frame['reg_period'].astype('str')

        # need to adjust for single char weeks, since 202252 is greater than 20251
        for index, value in reg_periods.items():
            if len(value) < 6:
                updated_reg_periods.update(
                    pd.Series([value[:4] + "0" + value[4:]], index=[index]))

        updated_reg_periods = updated_reg_periods.astype(
            'int').sort_values(ascending=False).astype('str')

        reg_periods = updated_reg_periods.head(num_weeks)

        old_frame = old_frame[old_frame['reg_period'].isin(reg_periods)]
        df = pd.concat([df, old_frame]).drop(columns=['guid']).drop_duplicates(
            subset=df.columns.difference(['time']))

    return {
        'ubw_customer_per_resource': df,
        'ubw_per_project_data': per_project_data,
        'ubw_per_customer_data': per_customer_data
    }

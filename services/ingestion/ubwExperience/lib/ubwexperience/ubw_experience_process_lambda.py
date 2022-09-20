import re
from dataplattform.common.aws import S3
from dataplattform.common.handlers.process import ProcessHandler
from typing import Dict
from datetime import datetime
import os
import pandas as pd
import numpy as np
from pathlib import PurePosixPath

handler = ProcessHandler()


@handler.process(partitions={})
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
        "resource_id",
        "name",
        "r0_x0023_exami0_x0023_612",
        "xr0_x0023_e1_x0023_611_x0023_U00",
        "date_from"
    ]
    experience_df = df.reindex(columns=col_selection_table)
    experience_df.rename(columns={
        'r0_x0023_exami0_x0023_612': 'examination_year',
        'xr0_x0023_e1_x0023_611_x0023_U00': 'grade',
        'resource_id': 'alias'}, inplace=True)

    def get_experience(data):
        experiences = []
        for (index, row) in data.iterrows():
            examination_year = row["examination_year"]
            work_start = int(row["date_from"][:4])
            if pd.isna(examination_year) or work_start == 0:
                experience = -1
            else:
                experience = int(work_start) - int(examination_year)

            person = dict(row)
            person["experience"] = experience
            experiences.append(person)
        return pd.DataFrame(experiences)

    ubw_experience = get_experience(experience_df)
    print("working!!!", ubw_experience)

    return {
        'ubw_experience': ubw_experience
     }

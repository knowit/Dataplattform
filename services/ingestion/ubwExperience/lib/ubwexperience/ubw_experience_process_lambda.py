import re
from dataplattform.common.aws import S3
from dataplattform.common.handlers.process import ProcessHandler
from typing import Dict
from datetime import datetime
from datetime import date
import os
import pandas as pd
import numpy as np
from pathlib import PurePosixPath

handler = ProcessHandler()


@handler.process(partitions={}, overwrite=True, overwrite_all_versions=True)
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
        "experience",
        "r0_x0023_exami0_x0023_612",
        "xr0_x0023_e1_x0023_611_x0023_U00",
        "date_from"
    ]
    experience_df = df.reindex(columns=col_selection_table)
    experience_df.rename(columns={
        'r0_x0023_exami0_x0023_612': 'examination_year',
        'xr0_x0023_e1_x0023_611_x0023_U00': 'grade',
        'resource_id': 'alias',
        'date_from': 'start_year'}, inplace=True)

    def get_experience(data):
        experiences = []
        current_year = date.today().year
        for (index, row) in data.iterrows():
            person = dict(row)

            examination_year = row["examination_year"]
            
            if not pd.isna(examination_year) and examination_year != "0":
                experience = current_year - int(examination_year)
            else:
                experience = 0

            person["experience"] = experience
            experiences.append(person)

        return pd.DataFrame(experiences)

    ubw_experience = get_experience(experience_df)
    print("Sucessful, reading ", len(ubw_experience), "people")

    return {
        'ubw_experience': ubw_experience
     }

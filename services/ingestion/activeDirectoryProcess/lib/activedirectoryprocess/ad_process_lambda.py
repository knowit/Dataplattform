import boto3
import pandas as pd

from os import environ
from dataplattform.common.handlers.process import ProcessHandler
from typing import Dict
from datetime import datetime
handler = ProcessHandler()


@handler.process(partitions={}, overwrite=True, overwrite_all_versions=True,
                 historical_tables=['ad_number_of_employees'])
def process(data, events) -> Dict[str, pd.DataFrame]:
    db = boto3.resource('dynamodb')
    person_data_table = db.Table(environ.get('PERSON_DATA_TABLE'))
    persons = pd.DataFrame(person_data_table.scan()['Items'])
    persons_filtered = persons[['guid', 'displayName', 'email', 'manager', 'manager_email']]
    number_of_employees = len(persons_filtered)
    ad_num_employees = pd.DataFrame({'time': int(datetime.now().timestamp()),
                                     'number_of_employees': number_of_employees}, index=[0])

    return {
        'active_directory': persons_filtered,
        'ad_number_of_employees': ad_num_employees
    }

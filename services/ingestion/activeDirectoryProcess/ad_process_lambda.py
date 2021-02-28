import boto3
import pandas as pd

from os import environ
from dataplattform.common.handlers.process import ProcessHandler
from typing import Dict

handler = ProcessHandler()


@handler.process(partitions={}, overwrite=True, overwrite_all_versions=True)
def process(data, events) -> Dict[str, pd.DataFrame]:
    db = boto3.resource('dynamodb')
    person_data_table = db.Table(environ.get('PERSON_DATA_TABLE'))
    persons = pd.DataFrame(person_data_table.scan()['Items'])
    persons_filtered = persons[['guid', 'displayName', 'email', 'manager']]
    return {
        'active_directory': persons_filtered
    }

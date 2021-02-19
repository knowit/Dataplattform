import boto3
import pandas as pd

from os import environ
from dataplattform.common.handlers.process import ProcessHandler
from typing import Dict

handler = ProcessHandler()


@handler.process(partitions={})
def process(data, events) -> Dict[str, pd.DataFrame]:
    db = boto3.resource('dynamodb')
    person_data_table = db.Table(environ.get('PERSON_DATA_TABLE'))
    persons = person_data_table.scan()['Items']
    persons_filtered = []
    for person in persons:
        persons_filtered.append({
            'guid': person['guid'],
            'displayName': person['displayName'],
            'email': person['email'],
            'alias': person['alias']
        })
    return {
        'active_directory': pd.DataFrame(persons_filtered)
    }

from enum import Enum
from os import environ
import boto3
from boto3.dynamodb.conditions import Attr


class PersonIdentifierType(Enum):
    GUID = 'guid'
    EMAIL = 'email'
    ALIAS = 'alias'
    FULL_NAME = 'full_name'


class PersonRepository():
    table_name = 'personal_metadata_table'

    def __enter__(self):
        self.db = boto3.resource('dynamodb')
        return self

    def __exit__(self, type_, value, traceback):
        pass

    @property
    def table(self):
        return self.db.Table(f'{environ.get("STAGE", "dev")}_{self.table_name}')

    def get_guid_by(self, id_type: PersonIdentifierType, value: str):
        if (id_type == PersonIdentifierType.GUID):
            return value

        response = self.table.scan(
            FilterExpression=Attr(id_type.value).eq(value)
        )
        return response['Items'][0]['guid']

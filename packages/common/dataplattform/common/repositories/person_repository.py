from enum import Enum
from os import environ
import boto3
from boto3.dynamodb.conditions import Attr


class PersonIdentifierType(Enum):
    GUID = 'guid'
    EMAIL = 'email'
    ALIAS = 'alias'
    FULL_NAME = 'full_name'


class PersonRepository:
    def __enter__(self):
        self.db = boto3.resource('dynamodb')
        return self

    def __exit__(self, type_, value, traceback):
        pass

    @property
    def table(self):
        return self.db.Table(environ.get('PERSON_DATA_TABLE'))

    def get_guid_by(self, id_type: PersonIdentifierType, value: str):
        if id_type == PersonIdentifierType.GUID:
            return value

        response = self.table.scan(
            FilterExpression=Attr(id_type.value).eq(value)
        )

        if len(response.get('Items', [])) == 0:
            return ""
        return response.get('Items', [])[0].get('guid', "")

    def get_manager_by(self, id_type: PersonIdentifierType, value: str):
        response = self.table.scan(
            FilterExpression=Attr(id_type.value).eq(value)
        )

        if len(response.get('Items', [])) == 0:
            return ""
        return response.get('Items', [])[0].get('manager', "")

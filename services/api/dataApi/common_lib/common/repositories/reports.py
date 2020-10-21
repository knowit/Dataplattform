from common.repositories.dynamo_db import DynamoDBRepository
from os import environ
from datetime import datetime


class ReportsRepository(DynamoDBRepository):
    table_name = 'reports_table'

    @property
    def table(self):
        return self.db.Table(f'{environ.get("STAGE", "dev")}_{self.table_name}')

    def get(self, name: str):
        response = self.table.get_item(
            Key={'name': name}
        )
        return response['Item']

    def all(self):
        response = self.table.scan()
        return response['Items']

    def create(self, model):
        now = datetime.now()
        self.table.put_item(
            Item={
                'name': model['name'],
                'queryString': model['queryString'],
                'tables':  model['tables'],
                'dataProtection': model['dataProtection'],
                'created': now.isoformat(),
                'lastUsed': None,
                'lastCacheUpdate': now.isoformat()
            },
            Expected={
                'name': {'Exists': False}
            }
        )
        return True

    def delete(self, name: str):
        self.table.delete_item(
            Key={'name': name}
        )
        return True

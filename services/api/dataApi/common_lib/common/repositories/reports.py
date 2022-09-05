from datetime import datetime
from os import environ
from typing import List

from boto3.dynamodb.conditions import Key
from common.repositories.dynamo_db import DynamoDBRepository


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

    def get_by_tables(self, tables: List[str]):

        def compare_table(table):
            return table in tables

        result = filter(lambda report: any(compare_table(t) for t in report['tables']), self.all())
        return list(result)

    def all(self):
        response = self.table.scan()
        return response['Items']

    def create(self, model):
        now = datetime.now()
        self.table.put_item(
            Item={
                'name': model['name'],
                'queryString': model['queryString'],
                'tables': model['tables'],
                'dataProtection': model['dataProtection'],
                'created': now.isoformat(),
            },
            Expected={
                'name': {'Exists': False}
            }
        )
        return True

    def update_cache_time(self, name: str):
        from botocore.exceptions import ClientError
        now = datetime.now()
        try:
            self.table.update_item(
                Key={'name': name},
                UpdateExpression="set lastCacheUpdate = :now",
                ExpressionAttributeValues={
                    ':now': now.isoformat()
                },
                ConditionExpression=Key("name").eq(name)
            )
        except ClientError as e:
            if e.response['Error']['Code'] == "ConditionalCheckFailedException":
                raise KeyError("Could not find report with name: " + name) from e
            else:
                raise

    def delete(self, name: str):
        self.table.delete_item(
            Key={'name': name}
        )
        return True

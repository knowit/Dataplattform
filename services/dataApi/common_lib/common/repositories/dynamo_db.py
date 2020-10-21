import boto3


class DynamoDBRepository:
    def __enter__(self):
        self.db = boto3.resource('dynamodb')
        return self

    def __exit__(self, type_, value, traceback):
        pass

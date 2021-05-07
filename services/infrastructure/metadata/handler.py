import boto3
import os


def mock(event, context):
    try:
        dynamodb = boto3.resource('dynamodb')
        table_name = os.environ['STAGE'] + '_personal_metadata_table'
        table = dynamodb.Table(table_name)
        base = ord('A')
        base_lower = ord('a')
        with table.batch_writer() as batch:
            for i in range(10):
                batch.put_item(
                    Item={
                        'guid': '000000000000000000000000000000000000000' + str(i),
                        'alias': 'alias' + chr(base_lower + i),
                        'company': 'Sample Company ' + chr(base + (i // 5)),
                        'displayName': 'Navn ' + chr(base + i) + '. Navnesen ',
                        'distinguished_name': 'Navn ' + chr(base + i) + '. Navnesen ',
                        'email': 'navn.' + chr(base_lower + i) + '.navnesen@smplcompany.' + chr(base_lower + (i // 5)) + '.no',
                        'knowitBranch': 'Branchname ' + chr(base + (i // 5)),
                        'manager': 'Ola ' + chr(base + (i // 4)) + '. Nordmann '
                    }
                )

        return dict(
            statusCode=200
        )
    except Exception as e:
        return dict(
            statusCode=500,
            body=str(e)
        )

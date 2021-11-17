import boto3
import os
from faker import Faker

fake = Faker('no_NO')
Faker.seed(123456)


def mock(event, context):
    try:
        dynamodb = boto3.resource('dynamodb')
        table_name = os.environ['STAGE'] + '_personal_metadata_table'
        table = dynamodb.Table(table_name)

        with table.batch_writer() as batch:
            sub_divisions = ['Objectnet', 'Experience']

            for i in range(10):
                first_name = fake.first_name()
                last_name = fake.last_name()
                knowit_branch = sub_divisions[i % 2]

                guid = fake.sha1()
                alias = f'{str.lower(first_name[:3])}{str.lower(last_name[:3])}'
                company = f'Knowit {knowit_branch}'
                display_name = f'{first_name} {last_name}'
                distinguished_name = display_name
                email = f'{str.lower(first_name)}.{str.lower(last_name)}@knowit.no'
                manager = fake.name()

                batch.put_item(
                    Item={
                        'guid': guid,
                        'alias': alias,
                        'company': company,
                        'displayName': display_name,
                        'distinguished_name': distinguished_name,
                        'email': email,
                        'knowitBranch': knowit_branch,
                        'manager': manager
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

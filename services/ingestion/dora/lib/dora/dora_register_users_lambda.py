import boto3
from botocore.exceptions import ClientError
import pandas as pd
import io
from os import environ

quicksight_client = boto3.client('quicksight')
sts_client = boto3.client('sts')
account_id = sts_client.get_caller_identity().get('Account')
s3 = boto3.resource('s3')
s3_client = boto3.client('s3')

csv = "data/level-3/dora/dora_users.csv"
s3_bucket = environ.get('DATALAKE')
namespace = 'default'


def handler(event, context):
    def get_existing_users():
        return quicksight_client.list_users(
            AwsAccountId=account_id,
            Namespace='default'
        ).get('UserList')

    def get_all_users():
        csv_file = s3_client.get_object(Bucket=s3_bucket, Key=csv)
        csv_string = csv_file['Body'].read().decode('utf-8')
        return pd.read_csv(io.StringIO(csv_string)).to_dict('records')

    def register_user(user_name, email):
        quicksight_client.register_user(
            IdentityType='QUICKSIGHT',
            Email=email,
            UserRole='READER',
            AwsAccountId=account_id,
            Namespace=namespace,
            UserName=user_name,
        )

    def get_user_group_names(user_name):
        user_groups = quicksight_client.list_user_groups(
            UserName=user_name,
            AwsAccountId=account_id,
            Namespace=namespace
        )
        return [group['GroupName'] for group in user_groups['GroupList']]

    def create_group_membership(user_name, group_name):
        quicksight_client.create_group_membership(
            MemberName=user_name,
            GroupName=group_name,
            AwsAccountId=account_id,
            Namespace='default'
        )

    def delete_user(user_name):
        quicksight_client.delete_user(
            UserName=user_name,
            AwsAccountId=account_id,
            Namespace=namespace
        )

    def describe_user(user_name):
        response = quicksight_client.describe_user(
            UserName=user_name,
            AwsAccountId=account_id,
            Namespace=namespace
        )
        return response

    def register_new_users():
        existing_usernames = [user['UserName'] for user in get_existing_users()]
        all_users = get_all_users()

        for user in all_users:
            user_name = user['UserName']
            try:
                if user_name not in existing_usernames:
                    register_user(user_name, user['Email'])

                user_groups = get_user_group_names(user_name)

                if user['Group'] not in user_groups:
                    create_group_membership(user_name, user['Group'])

            except ClientError as error:
                raise error

        users_to_delete = set(existing_usernames) - set([user['UserName'] for user in all_users])

        for user_name in users_to_delete:
            user = describe_user(user_name)
            if user['User']['Role'] != 'ADMIN':
                delete_user(user_name)

    register_new_users()

    return {
        'message': 'success!'
    }

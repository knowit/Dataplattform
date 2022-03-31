import boto3
from os import environ

def migrate_user(event, context):
    try:
        client = boto3.client('cognito-idp')
        client.admin_add_user_to_group(
            UserPoolId=environ['USER_POOL_ID'],
            Username=event['userName'],
            GroupName='level1'
        )
        return event
    except Exception as e:
        return dict(
            statusCode=500,
            body=str(e)
        )

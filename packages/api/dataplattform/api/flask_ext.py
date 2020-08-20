import boto3
import botocore
import datetime
from dateutil.tz import tzlocal
from flask import Flask, request
import re


def create_session(role_arn: str, base_session=None):
    base_session = base_session or boto3.session.Session()._session
    fetcher = botocore.credentials.AssumeRoleCredentialFetcher(
        client_creator=base_session.create_client,
        source_credentials=base_session.get_credentials(),
        role_arn=role_arn)
    creds = botocore.credentials.DeferredRefreshableCredentials(
        method='assume-role',
        refresh_using=fetcher.fetch_credentials,
        time_fetcher=lambda: datetime.datetime.now(tzlocal()))

    botocore_session = botocore.session.Session()
    botocore_session._credentials = creds
    return boto3.Session(botocore_session=botocore_session)


class UserSession(object):
    def __init__(self, app: Flask = None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask):
        app.before_request(self.assume_role)

    def user_claims(self):
        event = request.environ.get('serverless.event', {})
        return event.get('requestContext', {}).get('authorizer', {}).get('claims', None)

    def cognito_group(self):
        claims = self.user_claims()
        if claims:
            cognito_client = boto3.client('cognito-idp')
            response = cognito_client.get_group(GroupName=re.sub(r"[\[\]]", "", claims['cognito:groups']),
                                                UserPoolId=claims['iss'].split('/')[-1])
            return response['Group']
        return None

    def boto_session(self):
        group = self.cognito_group()
        return create_session(group['RoleArn']) if group else boto3._get_default_session()

    def assume_role(self):
        boto3.setup_default_session(botocore_session=self.boto_session()._session)

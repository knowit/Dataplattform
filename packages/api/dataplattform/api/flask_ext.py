import boto3
import botocore
import datetime
from dateutil.tz import tzlocal
from flask import Flask, request
import re
from cachetools import cached, TTLCache


class UserSession(object):
    def __init__(self, app: Flask = None, assume_user_role=True):
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask, assume_user_role=True):
        self.base_session = boto3._get_default_session()
        if assume_user_role:
            app.before_request(self.assume_role)

    def assume_role(self):
        boto3.DEFAULT_SESSION = self.boto_session

    @property
    def user_claims(self):
        event = request.environ.get('serverless.event', {})
        return event.get('requestContext', {}).get('authorizer', {}).get('claims', None)

    @property
    def boto_session(self):
        claims = self.user_claims
        if claims:
            group = self.cognito_group(claims.get('cognito:groups', ''), claims.get('iss', ''))
            if group:
                return self.create_boto_session(group['RoleArn'])
        return boto3.setup_default_session()

    @cached(TTLCache(maxsize=10, ttl=60))
    def cognito_group(self, group: str, iss: str):
        if group and iss:
            cognito_client = self.base_session.client('cognito-idp')
            response = cognito_client.get_group(
                GroupName=re.sub(r"[\[\]]", "", group),
                UserPoolId=iss.split('/')[-1])
            return response.get('Group', None)
        return None

    @cached(TTLCache(maxsize=10, ttl=60))
    def create_boto_session(self, role_arn: str):
        fetcher = botocore.credentials.AssumeRoleCredentialFetcher(
            client_creator=self.base_session._session.create_client,
            source_credentials=self.base_session._session.get_credentials(),
            role_arn=role_arn)
        creds = botocore.credentials.DeferredRefreshableCredentials(
            method='assume-role',
            refresh_using=fetcher.fetch_credentials,
            time_fetcher=lambda: datetime.datetime.now(tzlocal()))

        botocore_session = botocore.session.Session()
        botocore_session._credentials = creds
        return boto3.Session(botocore_session=botocore_session)

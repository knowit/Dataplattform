from pytest import fixture, hookimpl
from moto import mock_s3, mock_ssm, mock_iam
from boto3 import resource, client, setup_default_session
from os import environ
from unittest.mock import patch, MagicMock
import json
from uuid import uuid4
from dataplattform.testing.util import ignore_policy


def pytest_addoption(parser):
    parser.addini(
        'dataplattform-aws-ssm',
        type='linelist',
        help='',
        default=[]
        )


@hookimpl(tryfirst=True)
def pytest_load_initial_conftests(args, early_config, parser):
    if 'AWS_DEFAULT_REGION' not in environ:
        environ['AWS_DEFAULT_REGION'] = 'eu-central-1'

    # Ensure mocked AWS env
    environ.pop('AWS_ACCESS_KEY_ID', None)
    environ.pop('AWS_SECRET_ACCESS_KEY', None)
    environ.pop('AWS_SECURITY_TOKEN', None)
    environ.pop('AWS_SESSION_TOKEN', None)

    # Default test env
    default_env = [
        ('DATALAKE', 'testlake'),
        ('ACCESS_PATH', 'data/test/'),
        ('STAGE', 'dev'),
        ('SERVICE', 'testService')
    ]
    for key, value in default_env:
        if key not in environ:
            environ[key] = value


@fixture(autouse=True)
def iam_user():
    with mock_iam():
        iam = client('iam')
        mock_user = f'TEST_USER_{str(uuid4())}'

        with ignore_policy():
            iam.create_user(UserName=mock_user)
            iam.attach_user_policy(
                PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
                UserName=mock_user)
            test_access_keys = iam.create_access_key(UserName=mock_user)['AccessKey']

        class MockUserSetup:
            @staticmethod
            def ensure_mock_session():
                setup_default_session(aws_access_key_id=test_access_keys['AccessKeyId'],
                                      aws_secret_access_key=test_access_keys['SecretAccessKey'])
                environ['AWS_ACCESS_KEY_ID'] = test_access_keys['AccessKeyId']
                environ['AWS_SECRET_ACCESS_KEY'] = test_access_keys['SecretAccessKey']

            @staticmethod
            def use_policy(action, *actions, resource=['*']):
                with ignore_policy():
                    policy_document = json.dumps({
                            'Version': '2012-10-17',
                            'Statement': [{
                                'Effect': 'Allow',
                                'Action': [action] + list(actions),
                                'Resource': resource
                            }]
                        })
                    policy = iam.create_policy(
                        PolicyName=f'TEST_POLICY_{str(uuid4())}',
                        PolicyDocument=policy_document)['Policy']
                    iam.attach_user_policy(
                        PolicyArn=policy['Arn'],
                        UserName=mock_user)

            @staticmethod
            def use_serverless_policy():
                # print(pytestconfig.rootdir)
                raise NotImplementedError

        MockUserSetup.ensure_mock_session()
        yield MockUserSetup


@fixture(autouse=True)
def ssm_client(iam_user, pytestconfig):
    with mock_ssm():
        iam_user.ensure_mock_session()
        ssm = client('ssm')
        for e in pytestconfig.getini('dataplattform-aws-ssm'):
            key, _, value = e.partition('=')

            key = key.strip()
            type_, _, value = value.partition(':')
            with ignore_policy():
                ssm.put_parameter(
                    Name=key,
                    Value=value.strip(),
                    Type=type_.strip(),
                    Tier='Standard')

        yield ssm


@fixture(autouse=True)
def s3_bucket(iam_user):
    with mock_s3():
        iam_user.ensure_mock_session()
        s3 = resource('s3')
        with ignore_policy():
            s3.create_bucket(Bucket=environ.get('DATALAKE'))
        yield s3.Bucket(environ.get('DATALAKE'))


@fixture(autouse=True)
def athena():
    class AthenaMocker:
        def on_query(self, query, result):
            sql = query.get_sql() if hasattr(query, 'get_sql') else query
            self.mock_all = False
            self.result_table[sql] = result

        def __enter__(self):
            def on_execute(cursor, sql, *a, **kwargs):
                if sql in self.result_table:
                    mock = MagicMock()
                    mock.as_pandas.return_value = self.result_table[sql]
                    return mock
                elif self.mock_all:
                    return MagicMock()
                else:
                    raise Exception(f'No mock for query: {sql}')

            self.patcher = patch('pyathena.pandas_cursor.PandasCursor.execute', new=on_execute)
            self.patcher.start()
            self.result_table = {}
            self.mock_all = True
            return self

        def __exit__(self, type_, value, traceback):
            self.patcher.stop()
            return type_ is None

    with AthenaMocker() as athena_mocker:
        yield athena_mocker


@fixture
def create_table_mock(mocker):
    on_to_parquet_stub = mocker.stub()
    mocker.patch(
        'pandas.DataFrame.to_parquet',
        new=lambda *args, **kwargs: on_to_parquet_stub(*args, **kwargs))

    def assert_table_created(*tables):
        tables = [f'structured/{t}' for t in tables]
        assert all([t == tables[i] for i, ((_, t, ), _) in enumerate(on_to_parquet_stub.call_args_list)])

    def assert_table_data(table, df, **kwargs):
        from pandas.testing import assert_frame_equal
        table = f'structured/{table}'
        actual_df = next(iter([df for (df, t, ), _ in on_to_parquet_stub.call_args_list if table == t]), None)
        if actual_df is None:
            assert False, f'no create call with {table}'
        assert_frame_equal(actual_df, df, check_index_type=False, **kwargs)

    def assert_table_data_column(table, column, ser, **kwargs):
        from pandas.testing import assert_series_equal
        table = f'structured/{table}'
        actual_df = next(iter([df for (df, t, ), _ in on_to_parquet_stub.call_args_list if table == t]), None)
        if actual_df is None:
            assert False, f'no create call with {table}'
        assert_series_equal(actual_df[column], ser, check_index_type=False, check_names=False, **kwargs)

    on_to_parquet_stub.assert_table_created = assert_table_created
    on_to_parquet_stub.assert_table_data = assert_table_data
    on_to_parquet_stub.assert_table_data_column = assert_table_data_column

    yield on_to_parquet_stub

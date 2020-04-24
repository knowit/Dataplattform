from pytest import fixture, hookimpl
from moto import mock_s3, mock_ssm
from boto3 import resource, client
from os import environ
from unittest.mock import patch, MagicMock


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
    environ['AWS_ACCESS_KEY_ID'] = 'testing'
    environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    environ['AWS_SECURITY_TOKEN'] = 'testing'
    environ['AWS_SESSION_TOKEN'] = 'testing'

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
def ssm_client(pytestconfig):
    with mock_ssm():
        ssm = client('ssm')
        for e in pytestconfig.getini('dataplattform-aws-ssm'):
            key, _, value = e.partition('=')

            key = key.strip()
            type_, _, value = value.partition(':')

            ssm.put_parameter(
                Name=key,
                Value=value.strip(),
                Type=type_.strip(),
                Tier='Standard')

        yield ssm


@fixture(autouse=True)
def s3_bucket():
    with mock_s3():
        s3 = resource('s3')
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

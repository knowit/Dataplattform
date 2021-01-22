from pytest import fixture, hookimpl
from moto import mock_s3, mock_ssm, mock_sqs, mock_sns
from boto3 import resource, client
from os import environ
from unittest.mock import patch, MagicMock


def pytest_addoption(parser):
    parser.addini('dataplattform-aws-ssm', type='linelist', help='', default=[])


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
        ('SERVICE', 'testService'),
        ('SQS_QUEUE_NAME', 'test.fifo'),
        ('SQS_MESSAGE_GROUP_ID', 'test_groud_id'),
        ('PRIVATE_BUCKET', 'private_test_bucket'),
        ('PUBLIC_BUCKET', 'public_test_bucket'),
        ('DOWNLOAD_LAMBDA', 'test_download_lambda'),
        ('SNS_TOPIC_NAME', 'test_sns_topic'),
        ('PUBLIC_PREFIX', 'public/images'),
        ('PRIVATE_PREFIX', 'private/cvs'),
        ('ACCESS_LEVEL', 'level-1')
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
                Name=key, Value=value.strip(), Type=type_.strip(), Tier='Standard'
            )

        yield ssm


@fixture(autouse=True)
def s3_buckets():
    with mock_s3():
        s3 = resource('s3')
        s3.create_bucket(Bucket=environ.get('DATALAKE'))
        s3.create_bucket(Bucket=environ.get('PRIVATE_BUCKET'))
        s3.create_bucket(Bucket=environ.get('PUBLIC_BUCKET'))
        yield {
                "datalake": s3.Bucket(environ.get('DATALAKE')),
                "private_bucket": s3.Bucket(environ.get('PRIVATE_BUCKET')),
                "public_bucket": s3.Bucket(environ.get('PUBLIC_BUCKET'))
              }


@fixture
def s3_bucket(s3_buckets):
    yield s3_buckets['datalake']


@fixture
def s3_public_bucket(s3_buckets):
    yield s3_buckets['public_bucket']


@fixture
def s3_private_bucket(s3_buckets):
    yield s3_buckets['private_bucket']


@fixture(autouse=True)
def sqs_queue():
    with mock_sqs():
        sqs = resource('sqs')
        sqs.create_queue(QueueName=environ.get('SQS_QUEUE_NAME'))
        yield sqs.get_queue_by_name(QueueName=environ.get('SQS_QUEUE_NAME'))


@fixture(autouse=True)
def sns_topic():
    with mock_sns():
        sns = resource('sns')
        topic = sns.create_topic(Name=environ.get('SNS_TOPIC_NAME'))
        environ['DATA_UPDATE_TOPIC'] = topic.arn
        environ['NEW_REPORT_TOPIC'] = topic.arn
        environ['DELETE_REPORT_TOPIC'] = topic.arn
        yield topic


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

            self.patcher = patch(
                'pyathena.pandas_cursor.PandasCursor.execute', new=on_execute
            )
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
        new=lambda *args, **kwargs: on_to_parquet_stub(*args, **kwargs),
    )

    def assert_table_created(*tables):
        tables = [f'structured/{t}' for t in tables]
        if len(tables) == 0:
            assert False, 'No tables provided'

        if len(on_to_parquet_stub.call_args_list) == 0:
            assert False, 'on_to_parquet not called'
        if len(on_to_parquet_stub.call_args_list) != len(tables):
            assert False, 'Number of tables provided does not equal number of on_to_parquet calls'

        error_msg = 'No tables created, or wrong naming of tables provided'
        assert all([t == tables[i] for i, ((_, t, ), _) in enumerate(on_to_parquet_stub.call_args_list)]), error_msg

    def assert_table_not_created(*tables):
        tables = [f'structured/{t}' for t in tables]
        if len(on_to_parquet_stub.call_args_list) == 0:
            assert True, 'No tables are created'

        error_msg = 'One or more tables are created'
        assert all([t != tables[i] for i, ((_, t, ), _) in enumerate(on_to_parquet_stub.call_args_list)]), error_msg

    def df_from_calls(table):
        from pandas import concat

        actual_df_list = [
            df for (df, t,), _ in on_to_parquet_stub.call_args_list if table == t
        ]
        if not actual_df_list:
            assert False, f'no create call with {table}'
        return concat(actual_df_list)

    def assert_table_data(table, df, **kwargs):
        from pandas.testing import assert_frame_equal

        assert_frame_equal(
            df_from_calls(f'structured/{table}'), df, check_index_type=False, **kwargs
        )

    def assert_table_data_column(table, column, ser, **kwargs):
        from pandas.testing import assert_series_equal

        assert_series_equal(
            df_from_calls(f'structured/{table}').reset_index()[column],
            ser,
            check_index_type=False,
            check_names=False,
            **kwargs,
        )

    def assert_table_data_contains_df(table, df, **kwargs):
        import string
        import random
        import numpy as np
        # pandas.isin() does not support comparing dataframes with null/nullable values.
        # Comparing two dataframes containing null at the same locations will not work.
        # Therefor all nullable values in both dataframes are assigned to the same random value.

        df = df.astype(np.object)
        df_from_calls_object = df_from_calls(f'structured/{table}').astype(np.object)

        fill_value = ''.join(random.choices(string.ascii_uppercase +
                                            string.digits, k=7))
        input_df = df.fillna(fill_value)
        df_from_calls_object = df_from_calls_object.fillna(fill_value)
        tmp_df = input_df.isin(df_from_calls_object)
        assert tmp_df.eq(True).all().all(), "Dataframe is not contained in table, values differ"

    on_to_parquet_stub.assert_table_created = assert_table_created
    on_to_parquet_stub.assert_table_not_created = assert_table_not_created
    on_to_parquet_stub.assert_table_data = assert_table_data
    on_to_parquet_stub.assert_table_data_column = assert_table_data_column
    on_to_parquet_stub.assert_table_data_contains_df = assert_table_data_contains_df

    yield on_to_parquet_stub

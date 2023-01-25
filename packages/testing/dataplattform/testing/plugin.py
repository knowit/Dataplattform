from pytest import fixture, hookimpl
from moto import mock_s3, mock_ssm, mock_sqs, mock_sns, mock_dynamodb2
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
        ('PUBLIC_BUCKET', 'public_test_bucket'),
        ('DOWNLOAD_LAMBDA', 'test_download_lambda'),
        ('SNS_TOPIC_NAME', 'test_sns_topic'),
        ('PUBLIC_PREFIX', 'public/images'),
        ('ACCESS_LEVEL', 'level-1'),
        ('PERSON_DATA_TABLE', 'my_test_person_data_table'),
        ('AWS_XRAY_SDK_ENABLED', 'false'),
    ]
    for key, value in default_env:
        if key not in environ:
            environ[key] = value


@fixture
def db_person_data():
    yield [
        {'guid': '20dbbfa18380233aa643575720b893fac5137699', 'email': 'per.nordmann@knowit.no',
         'displayName': 'Per Nordmann', 'alias': 'pernord', 'company': 'Knowit Objectnet', 'knowitBranch': 'Solutions',
         'distinguished_name': 'Per Nordmann', 'manager': 'Olav Nordmann', 'title': 'Consultatnt'},

        {'guid': '491b9fa9bfac17563882b0fdc6f3a8a97417bd99', 'email': 'kari.nordmann@knowit.no',
         'displayName': 'Kari Nordmann', 'alias': 'karnord', 'company': 'Knowit Objectnet', 'knowitBranch': 'Solutions',
         'distinguished_name': 'Kari Nordmann', 'manager': 'Olav Nordmann', 'title': 'Consultatnt'},

        {'guid': '5edbcdf460809039eb4897ccf8ce3bb5e501884d', 'email': 'lisa.nordmann@knowit.no',
         'displayName': 'Lisa Nordmann', 'alias': 'lisnord', 'company': 'Knowit Objectnet', 'knowitBranch': 'Solutions',
         'distinguished_name': 'Lisa Nordmann', 'manager': 'Per Nordmann', 'title': 'Consultatnt'},

        {'guid': 'b051b402346144a6cdcceb0027f6e80d29019f50', 'email': 'fredrik.arnesen@knowit.no',
         'displayName': 'Fredrik Arnesen', 'alias': 'frearn', 'company': 'Knowit Objectnet',
         'knowitBranch': 'Objectnet', 'distinguished_name': 'Fredrik Arnesen', 'manager': 'Karoline Hauge',
         'title': 'Consultatnt'},

        {'guid': '5d79f8b771cd4921b667f9227aece292213806d6', 'email': 'einar.halvorsen@knowit.no',
         'displayName': 'Einar Halvorsen', 'alias': 'einhal', 'company': 'Knowit Experience',
         'knowitBranch': 'Experience', 'distinguished_name': 'Einar Halvorsen', 'manager': 'Marie Lie',
         'title': 'Consultatnt'},

        {'guid': '0384e3914a44e044687fcdca9d6b18ebd9220780', 'email': 'ola.berge@knowit.no',
         'displayName': 'Ola Berge', 'alias': 'olaber', 'company': 'Knowit Objectnet',
         'knowitBranch': 'Objectnet', 'distinguished_name': 'Ola Berge', 'manager': 'Roar Arnesen',
         'title': 'Consultatnt'},

        {'guid': '792af2fabf0e6da9dc93ab4d647b2777ccb96ab8', 'email': 'daniel.bakke@knowit.no',
         'displayName': 'Daniel Bakke', 'alias': 'danbak', 'company': 'Knowit Experience',
         'knowitBranch': 'Experience', 'distinguished_name': 'Daniel Bakke', 'manager': 'Gunn Sandvik',
         'title': 'Consultatnt'},

        {'guid': '827a6b08afedcc15bc218b34f674b45e47bbf581', 'email': 'helge.engen@knowit.no',
         'displayName': 'Helge Engen', 'alias': 'heleng', 'company': 'Knowit Experience',
         'knowitBranch': 'Experience', 'distinguished_name': 'Helge Engen', 'manager': 'Christian Abrahamsen',
         'title': 'Consultatnt'},

        {'guid': '9880cb96df3cfa08887e497e9530755da4782e25', 'email': 'knut.ahmed@knowit.no',
         'displayName': 'Knut Ahmed', 'alias': 'knuahm', 'company': 'Knowit Objectnet',
         'knowitBranch': 'Objectnet', 'distinguished_name': 'Knut Ahmed', 'manager': 'Vegard Rasmussen',
         'title': 'Consultatnt'},

        {'guid': 'c5832e024008c2fac7a1e61dc56f192d980f660b', 'email': 'sander.ahmed@knowit.no',
         'displayName': 'Sander Ahmed', 'alias': 'sanahm', 'company': 'Knowit Objectnet',
         'knowitBranch': 'Objectnet', 'distinguished_name': 'Sander Ahmed', 'manager': 'Mette Antonsen',
         'title': 'Consultatnt'},

        {'guid': 'c7fd4b22dfce07f039d786be96b6caee5e0a8cf6', 'email': 'tor.amundsen@knowit.no',
         'displayName': 'Tor Amundsen', 'alias': 'toramu', 'company': 'Knowit Experience',
         'knowitBranch': 'Experience', 'distinguished_name': 'Tor Amundsen', 'manager': 'Camilla Lund',
         'title': 'Consultatnt'},

        {'guid': 'e0d071fbba5e8d5a6b7cca357006d2363f96a19a', 'email': 'cathrine.madsen@knowit.no',
         'displayName': 'Cathrine Madsen', 'alias': 'catmad', 'company': 'Knowit Experience',
         'knowitBranch': 'Experience', 'distinguished_name': 'Cathrine Madsen', 'manager': 'Tor Gundersen',
         'title': 'Consultatnt'},

        {'guid': 'faeb1af849a926d21bda012e4b3a971e1107fd0e', 'email': 'cathrine.kristiansen@knowit.no',
         'displayName': 'Cathrine Kristiansen', 'alias': 'catkri', 'company': 'Knowit Objectnet',
         'knowitBranch': 'Objectnet', 'distinguished_name': 'Cathrine Kristiansen', 'manager': 'Finn-Pål Myhre',
         'title': 'Consultatnt'}
    ]


@fixture()
def dynamodb_resource(db_person_data):
    with mock_dynamodb2():
        dynamodb_resource = resource('dynamodb')
        table = dynamodb_resource.create_table(
            TableName=environ.get('PERSON_DATA_TABLE'),
            KeySchema=[
                {
                    'AttributeName': "guid",
                    'KeyType': "HASH"  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': "guid",
                    'AttributeType': "S"
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 10
            }
        )
        for item in db_person_data:
            table.put_item(
                Item=item)
        yield table


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
        s3.create_bucket(Bucket=environ.get('PUBLIC_BUCKET'))
        yield {
                "datalake": s3.Bucket(environ.get('DATALAKE')),
                "public_bucket": s3.Bucket(environ.get('PUBLIC_BUCKET'))
              }


@fixture
def s3_bucket(s3_buckets):
    yield s3_buckets['datalake']


@fixture
def s3_public_bucket(s3_buckets):
    yield s3_buckets['public_bucket']


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
    on_to_parquet_stub.df_from_calls = df_from_calls

    yield on_to_parquet_stub

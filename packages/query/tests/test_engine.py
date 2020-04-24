from dataplattform.query import engine
from os import environ


def test_create_default_athena_engine():
    ath = engine.Athena()
    assert ath.default_database is None and \
        ath.staging_dir == 's3://testlake/data/test/stage'


def test_create_staging_dir_env_athena_engine():
    environ['STAGING_DIR'] = 's3://test/dir'

    ath = engine.Athena()
    assert ath.staging_dir == 's3://test/dir'


def test_create_params_athena_engine():
    ath = engine.Athena(bucket='testbucket', access_path='access/path')
    assert ath.staging_dir == 's3://testbucket/access/path/stage'


def test_create_default_database_athena_engine():
    ath = engine.Athena(default_database='myservice')
    assert ath.default_database == 'dev_myservice_database'


def test_get_tables_athena_engine():
    environ['DEFAULT_DATABASE'] = 'myservice'

    ath = engine.Athena()

    assert str(ath.table.test) == '"dev_myservice_database"."test"' and \
        str(ath.table['test']) == '"dev_myservice_database"."test"'


def test_get_tables_different_database_athena_engine():
    environ['DEFAULT_DATABASE'] = 'myservice'

    ath = engine.Athena()

    assert str(ath.table['test']) == '"dev_myservice_database"."test"' and \
        str(ath.table['other.test']) == '"dev_other_database"."test"'


def test_simple_sql():
    ath = engine.Athena()
    sql = ath.from_('my_table').select('test1', 'test2')
    assert str(sql) == 'SELECT "test1","test2" FROM "my_table"'


def test_simple_sql_with_table():
    ath = engine.Athena()
    my_table = ath.table.my_table

    assert ath.from_(my_table).select(my_table.test1, my_table.test2) ==\
        ath.from_('my_table').select('test1', 'test2')


def test_execute_query(mocker):
    cursor_mock = mocker.MagicMock()
    cursor_mock.execute = mocker.stub()

    ath = engine.Athena()
    ath.connection.cursor = mocker.MagicMock(return_value=cursor_mock)

    ath.from_('my_table').select('test1', 'test2').execute(ath)

    cursor_mock.execute.assert_called_with('SELECT "test1","test2" FROM "my_table"')

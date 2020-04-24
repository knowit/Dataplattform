from ubw_fag import handler
from pytest import fixture
from json import loads
import pandas as pd
from pandas.testing import assert_series_equal


@fixture(autouse=True)
def zeep_ubw_mock(mocker):
    mock = mocker.Mock()
    mock.service.GetTemplateResultAsXML.return_value = {
        "ReturnCode": 0,
        "Status": None,
        "TemplateResult": """
            <Agresso>
                <AgressoQE>
                    <_recno>0</_recno>
                    <_section>D</_section>
                    <tab>B</tab>
                    <reg_period>201817</reg_period>
                    <used_hrs>4</used_hrs>
                </AgressoQE>
                <AgressoQE>
                    <_recno>0</_recno>
                    <_section>D</_section>
                    <tab>B</tab>
                    <reg_period>201907</reg_period>
                    <used_hrs>1</used_hrs>
                </AgressoQE>
                <AgressoQE>
                    <_recno>0</_recno>
                    <_section>D</_section>
                    <tab>A</tab>
                    <reg_period>201907</reg_period>
                    <used_hrs>1</used_hrs>
                </AgressoQE>
            </Agresso>
        """
    }
    mocker.patch('ubw_fag.Client', return_value=mock)

    yield mock


def test_handler_metadata(s3_bucket):
    handler(None, None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())

    assert 'timestamp' in data['metadata']


def test_handler_data_length(s3_bucket):
    handler(None, None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())

    assert len(data['data']) == 2  # one filtered


def test_handler_data(s3_bucket, athena):
    handler(None, None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())

    assert data['data'][0]['tab'] == 'B' and\
        data['data'][0]['reg_period'] == '201817' and\
        data['data'][0]['used_hrs'] == '4'


def test_process_data(mocker):
    def on_to_parquet(df, *a, **kwa):
        assert_series_equal(
            df.reg_period,
            pd.Series(['201817', '201907'], index=[0, 1]),
            check_names=False)

    mocker.patch('pandas.DataFrame.to_parquet', new=on_to_parquet)
    handler(None, None)


def test_process_data_skip_existing(mocker, athena):
    athena.on_query(
        'SELECT "reg_period" FROM "dev_test_database"."ubw_fagtimer"',
        pd.DataFrame({'reg_period': ['201817']}))

    def on_to_parquet(df, *a, **kwa):
        assert_series_equal(
            df.reg_period,
            pd.Series(['201907'], index=[1]),
            check_names=False)

    mocker.patch('pandas.DataFrame.to_parquet', new=on_to_parquet)
    handler(None, None)

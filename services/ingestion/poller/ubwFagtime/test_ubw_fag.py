from ubw_fag import handler
from pytest import fixture
from json import loads
import pandas as pd


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


def test_handler_metadata(mocker, s3_bucket):
    handler(None, None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())

    assert 'timestamp' in data['metadata']


def test_handler_data_length(mocker, s3_bucket):
    handler(None, None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())

    assert len(data['data']) == 2  # one filtered


def test_handler_data(mocker, s3_bucket):
    handler(None, None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())

    assert data['data'][0]['tab'] == 'B' and\
        data['data'][0]['reg_period'] == '201817' and\
        data['data'][0]['used_hrs'] == '4'


def test_process_data(mocker, create_table_mock):
    handler(None, None)

    create_table_mock.assert_table_data_column(
        'ubw_fagtimer',
        'reg_period',
        pd.Series(['201817', '201907']))


def test_process_data_skip_existing(mocker, athena, create_table_mock):
    athena.on_query(
        'SELECT "reg_period" FROM "dev_test_database"."ubw_fagtimer"',
        pd.DataFrame({'reg_period': ['201817']}))

    handler(None, None)

    create_table_mock.assert_table_data_column(
        'ubw_fagtimer',
        'reg_period',
        pd.Series(['201907']))

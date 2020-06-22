from google_forms_webhook import handler
from dataplattform.testing.events import APIGateway
from json import loads
from os import path
from pytest import fixture
import pandas as pd


@fixture
def test_data_quiz():
    with open(path.join(path.dirname(__file__), 'test_data_quiz_single_respondent_valid_types.json'), 'r') as json_file:
        yield json_file.read()


@fixture
def test_data_quiz_invalid():
    with open(path.join(path.dirname(__file__), 'test_data_quiz_single_respondent_invalid.json'), 'r') as json_file:
        yield json_file.read()


@fixture
def test_data_form():
    with open(path.join(path.dirname(__file__), 'test_data_form.json'), 'r') as json_file:
        yield json_file.read()


@fixture
def test_data_form2():
    with open(path.join(path.dirname(__file__), 'test_data_form2.json'), 'r') as json_file:
        yield json_file.read()


@fixture
def test_data_form_multiple_respondents():
    with open(path.join(path.dirname(__file__), 'test_data_multiple_respondents.json'), 'r') as json_file:
        yield json_file.read()


def test_insert_data_quiz(s3_bucket, test_data_quiz, create_table_mock):
    handler(APIGateway(
        headers={},
        body=test_data_quiz).to_dict(), None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())
    assert data['data']['tableName'] == 'test_quiz'

    create_table_mock.assert_table_data_column(
        'test_test_quiz',
        'type',
        pd.Series(['SCALE',
                   'MULTIPLE_CHOICE',
                   'TEXT',
                   'CHECKBOX',
                   'MULTIPLE_CHOICE',
                   'LIST',
                   'DATE',
                   'TIME']))

    create_table_mock.assert_table_data_column(
        'test_test_quiz',
        'isQuiz',
        pd.Series([True,
                   True,
                   True,
                   True,
                   True,
                   True,
                   True,
                   True]))


def test_insert_data_form(s3_bucket, test_data_form, create_table_mock):
    handler(APIGateway(
        headers={},
        body=test_data_form).to_dict(), None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())
    assert data['data']['tableName'] == 'test_form'

    create_table_mock.assert_table_data_column(
        'test_test_form',
        'type',
        pd.Series(['PARAGRAPH_TEXT',
                   'TEXT',
                   'MULTIPLE_CHOICE',
                   'CHECKBOX',
                   'CHECKBOX',
                   'LIST',
                   'SCALE',
                   'GRID',
                   'GRID',
                   'CHECKBOX_GRID',
                   'CHECKBOX_GRID',
                   'DATE',
                   'TIME',
                   'FILE_UPLOAD']))


def test_insert_data_two_respondents(s3_bucket, test_data_form, test_data_form2, create_table_mock):
    handler(APIGateway(
        headers={},
        body=test_data_form).to_dict(), None)

    handler(APIGateway(
        headers={},
        body=test_data_form2).to_dict(), None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())
    assert data['data']['tableName'] == 'test_form'

    create_table_mock.assert_table_data_column(
        'test_test_form',
        'type',
        pd.Series(['PARAGRAPH_TEXT',
                   'TEXT',
                   'MULTIPLE_CHOICE',
                   'CHECKBOX',
                   'CHECKBOX',
                   'LIST',
                   'SCALE',
                   'GRID',
                   'GRID',
                   'CHECKBOX_GRID',
                   'CHECKBOX_GRID',
                   'DATE',
                   'TIME',
                   'FILE_UPLOAD',
                   'PARAGRAPH_TEXT',
                   'TEXT',
                   'MULTIPLE_CHOICE',
                   'CHECKBOX',
                   'LIST',
                   'SCALE',
                   'GRID',
                   'GRID',
                   'CHECKBOX_GRID',
                   'CHECKBOX_GRID',
                   'DATE',
                   'TIME',
                   'FILE_UPLOAD']))


def test_insert_data_invalid_type(s3_bucket, test_data_quiz_invalid, create_table_mock):
    handler(APIGateway(
        headers={},
        body=test_data_quiz_invalid).to_dict(), None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())
    assert data['data']['tableName'] == 'test_quiz'

    create_table_mock.assert_table_data_column(
        'test_test_quiz',
        'type',
        pd.Series(['MULTIPLE_CHOICE',
                   'TEXT',
                   'CHECKBOX',
                   'MULTIPLE_CHOICE',
                   'LIST',
                   'DATE',
                   'TIME']))


def test_insert_data_multiple_respondents(s3_bucket, test_data_form_multiple_respondents, create_table_mock):
    handler(APIGateway(
        headers={},
        body=test_data_form_multiple_respondents).to_dict(), None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())
    assert data['data']['tableName'] == 'test_form'

    create_table_mock.assert_table_data_column(
        'test_user_test_form',
        'type',
        pd.Series(['TEXT',
                   'PARAGRAPH_TEXT',
                   'TEXT',
                   'PARAGRAPH_TEXT',
                   ]))

    create_table_mock.assert_table_data_column(
        'test_user_test_form',
        'responder',
        pd.Series(['test_user1',
                   'test_user1',
                   'test_user2',
                   'test_user2',
                   ]))
    create_table_mock.assert_table_data_column(
        'test_user_test_form',
        'isQuiz',
        pd.Series([False,
                   False,
                   False,
                   False]))


def test_process_get_metadata(mocker, create_table_mock, test_data_form):
    handler(APIGateway(
        headers={},
        body=test_data_form).to_dict(), None)

    create_table_mock.assert_table_data_column(
        'google_forms_metadata',
        'uploaded_by_user',
        pd.Series(['test']))

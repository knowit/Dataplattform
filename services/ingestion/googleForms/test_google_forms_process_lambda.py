from google_forms_webhook_process_lambda import handler as processHandler
from dataplattform.common import schema
import os
from json import load
from pytest import fixture
import pandas as pd
import pytest


@fixture
def setup_queue_event(s3_bucket):
    def make_queue_event(data: schema.Data):
        s3_bucket.Object('/data/test.json').put(
            Body=data.to_json().encode('utf-8'))
        return {
            'Records': [{
                'body': '/data/test.json',
                'messageAttributes': {
                    's3FileName': {
                        'stringValue': '/data/test.json'
                    }
                }
            }]
        }
    yield make_queue_event


@fixture
def test_data_quiz():
    with open(os.path.join(os.path.dirname(__file__),
              'test_data_files/test_data_quiz_single_respondent_valid_types.json'), 'r') as json_file:
        yield load(json_file)


@fixture
def test_data_quiz_invalid():
    with open(os.path.join(os.path.dirname(__file__),
              'test_data_files/test_data_quiz_single_respondent_invalid.json'), 'r') as json_file:
        yield load(json_file)


@fixture
def test_data_form():
    with open(os.path.join(os.path.dirname(__file__), 'test_data_files/test_data_form.json'), 'r') as json_file:
        yield load(json_file)


@fixture
def test_data_form2():
    with open(os.path.join(os.path.dirname(__file__), 'test_data_files/test_data_form2.json'), 'r') as json_file:
        yield load(json_file)


@fixture
def test_data_empty():
    with open(os.path.join(os.path.dirname(__file__), 'test_data_files/test_data_empty.json'), 'r') as json_file:
        yield load(json_file)


@fixture
def test_data_form_multiple_respondents():
    with open(os.path.join(os.path.dirname(__file__),
              'test_data_files/test_data_multiple_respondents.json'), 'r') as json_file:
        yield load(json_file)


def test_insert_data_quiz_process(setup_queue_event, test_data_quiz, create_table_mock):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data_quiz))

    processHandler(event, None)

    create_table_mock.assert_table_data_column(
        'google_forms_data',
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
        'google_forms_data',
        'form_name',
        pd.Series(['test_quiz',
                   'test_quiz',
                   'test_quiz',
                   'test_quiz',
                   'test_quiz',
                   'test_quiz',
                   'test_quiz',
                   'test_quiz']))

    create_table_mock.assert_table_data_column(
        'google_forms_data',
        'uploaded_by_user',
        pd.Series(['test_person',
                   'test_person',
                   'test_person',
                   'test_person',
                   'test_person',
                   'test_person',
                   'test_person',
                   'test_person']))

    create_table_mock.assert_table_data_column(
        'google_forms_data',
        'is_quiz',
        pd.Series([True,
                   True,
                   True,
                   True,
                   True,
                   True,
                   True,
                   True]))


def test_insert_data_form(setup_queue_event, test_data_form, create_table_mock):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data_form))

    processHandler(event, None)

    create_table_mock.assert_table_data_column(
        'google_forms_data',
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


def test_insert_data_two_respondents(setup_queue_event, test_data_form, test_data_form2, create_table_mock):
    event1 = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data_form))

    processHandler(event1, None)

    event2 = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data_form2))

    processHandler(event2, None)

    create_table_mock.assert_table_data_column(
        'google_forms_data',
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


def test_insert_data_invalid_type(setup_queue_event, test_data_quiz_invalid, create_table_mock):
    invalid_file_quiz_event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data_quiz_invalid))

    with pytest.raises(KeyError):
        processHandler(invalid_file_quiz_event, None)


def test_insert_data_multiple_respondents(setup_queue_event, test_data_form_multiple_respondents, create_table_mock):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data_form_multiple_respondents))

    processHandler(event, None)

    create_table_mock.assert_table_data_column(
        'google_forms_data',
        'type',
        pd.Series(['TEXT',
                   'PARAGRAPH_TEXT',
                   'TEXT',
                   'PARAGRAPH_TEXT',
                   ]))

    create_table_mock.assert_table_data_column(
        'google_forms_data',
        'responder',
        pd.Series(['test_user1',
                   'test_user1',
                   'test_user2',
                   'test_user2',
                   ]))
    create_table_mock.assert_table_data_column(
        'google_forms_data',
        'is_quiz',
        pd.Series([False,
                   False,
                   False,
                   False]))


def test_process_no_responses_no_data_added(setup_queue_event, test_data_empty, create_table_mock):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data_empty))

    processHandler(event, None)

    create_table_mock.assert_table_not_created('google_forms_data')

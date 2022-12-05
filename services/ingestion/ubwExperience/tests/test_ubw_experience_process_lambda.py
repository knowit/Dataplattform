import os
from pathlib import PurePosixPath
from pytest import fixture
from ubwexperience.ubw_experience_process_lambda import handler
import pandas as pd
import numpy as np
import fastparquet as fp
import s3fs
from os import path
from json import load
from dataplattform.common import schema
from datetime import datetime, timedelta

@fixture
def test_data():
    with open(path.join(path.dirname(__file__), 'test_data.json'), 'r') as json_file:
        yield load(json_file)


@fixture
def test_data_old():
    with open(path.join(path.dirname(__file__), 'test_old_data.json'), 'r') as json_file:
        json = load(json_file)
        for i in range(len(json['data'])):  # Update reg_period to simulate recent data
            json['data'][i] = create_date_string(i)
        yield json

def create_date_string(num_weeks_back):
    date = datetime.now()
    delta = timedelta(weeks=num_weeks_back)
    tmp_year, tmp_week = (date - delta).isocalendar()[0:2]
    return str(tmp_year) + str(tmp_week)

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

def test_process_data_person_1(create_table_mock,
                               setup_queue_event,
                               test_data):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['person_1']))

    handler(event, None)
    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'alias',
        pd.Series(['FREARN']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'name',
        pd.Series(['Fredrik Arnesen']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'experience',
        pd.Series([32]))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'examination_year',
        pd.Series(['1990']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'grade',
        pd.Series(['Master of Science']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'start_year',
        pd.Series(['2020-03-16T00:00:00+01:00']))

    create_table_mock.assert_table_data(
        'ubw_experience',
        pd.DataFrame({
            'alias': ['FREARN'],
            'name': ['Fredrik Arnesen'],
            'experience': [32],
            'examination_year': ['1990'],
            'grade': ['Master of Science'],
            'start_year': ['2020-03-16T00:00:00+01:00']
        }))

def test_process_data_person_2(create_table_mock,
                               setup_queue_event,
                               test_data):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['person_2']))

    handler(event, None)
    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'alias',
        pd.Series(['EINHAL']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'name',
        pd.Series(['Einar Halvorsen']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'experience',
        pd.Series([22]))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'examination_year',
        pd.Series(['2000']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'grade',
        pd.Series(['Master of Science']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'start_year',
        pd.Series(['2020-03-16T00:00:00+01:00']))

    create_table_mock.assert_table_data(
        'ubw_experience',
        pd.DataFrame({
            'alias': ['EINHAL'],
            'name': ['Einar Halvorsen'],
            'experience': [22],
            'examination_year': ['2000'],
            'grade': ['Master of Science'],
            'start_year': ['2020-03-16T00:00:00+01:00']
        }))

def test_process_data_person_3(create_table_mock,
                               setup_queue_event,
                               test_data):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['person_3']))

    handler(event, None)
    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'alias',
        pd.Series(['SANAHM']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'name',
        pd.Series(['Sander Ahmed']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'experience',
        pd.Series([12]))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'examination_year',
        pd.Series(['2010']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'grade',
        pd.Series(['Master of Science']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'start_year',
        pd.Series(['2020-03-16T00:00:00+01:00']))

    create_table_mock.assert_table_data(
        'ubw_experience',
        pd.DataFrame({
            'alias': ['SANAHM'],
            'name': ['Sander Ahmed'],
            'experience': [12],
            'examination_year': ['2010'],
            'grade': ['Master of Science'],
            'start_year': ['2020-03-16T00:00:00+01:00']
        }))


def test_process_data_person_4(create_table_mock,
                               setup_queue_event,
                               test_data):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['person_4']))

    handler(event, None)
    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'alias',
        pd.Series(['CATKRI']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'name',
        pd.Series(['Cathrine Kristiansen']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'experience',
        pd.Series([42]))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'examination_year',
        pd.Series(['1980']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'grade',
        pd.Series(['Master of Science']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'start_year',
        pd.Series(['2020-03-16T00:00:00+01:00']))

    create_table_mock.assert_table_data(
        'ubw_experience',
        pd.DataFrame({
            'alias': ['CATKRI'],
            'name': ['Cathrine Kristiansen'],
            'experience': [42],
            'examination_year': ['1980'],
            'grade': ['Master of Science'],
            'start_year': ['2020-03-16T00:00:00+01:00']
        }))

def test_process_data_person_5(create_table_mock,
                               setup_queue_event,
                               test_data):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['person_5']))

    handler(event, None)
    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'alias',
        pd.Series(['TORAMU']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'name',
        pd.Series(['Tor Amundsen']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'experience',
        pd.Series([37]))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'examination_year',
        pd.Series(['1985']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'grade',
        pd.Series(['Master of Science']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'start_year',
        pd.Series(['2020-03-16T00:00:00+01:00']))

    create_table_mock.assert_table_data(
        'ubw_experience',
        pd.DataFrame({
            'alias': ['TORAMU'],
            'name': ['Tor Amundsen'],
            'experience': [37],
            'examination_year': ['1985'],
            'grade': ['Master of Science'],
            'start_year': ['2020-03-16T00:00:00+01:00']
        }))

def test_process_data_person_6(create_table_mock,
                               setup_queue_event,
                               test_data):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['person_6']))

    handler(event, None)
    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'alias',
        pd.Series(['CATMAD']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'name',
        pd.Series(['Cathrine Madsen']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'experience',
        pd.Series([27]))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'examination_year',
        pd.Series(['1995']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'grade',
        pd.Series(['Master of Science']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'start_year',
        pd.Series(['2020-03-16T00:00:00+01:00']))

    create_table_mock.assert_table_data(
        'ubw_experience',
        pd.DataFrame({
            'alias': ['CATMAD'],
            'name': ['Cathrine Madsen'],
            'experience': [27],
            'examination_year': ['1995'],
            'grade': ['Master of Science'],
            'start_year': ['2020-03-16T00:00:00+01:00']
        }))

def test_process_data_person_7(create_table_mock,
                               setup_queue_event,
                               test_data):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['person_7']))

    handler(event, None)
    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'alias',
        pd.Series(['DANBAK']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'name',
        pd.Series(['Daniel Bakke']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'experience',
        pd.Series([17]))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'examination_year',
        pd.Series(['2005']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'grade',
        pd.Series(['Master of Science']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'start_year',
        pd.Series(['2020-03-16T00:00:00+01:00']))

    create_table_mock.assert_table_data(
        'ubw_experience',
        pd.DataFrame({
            'alias': ['DANBAK'],
            'name': ['Daniel Bakke'],
            'experience': [17],
            'examination_year': ['2005'],
            'grade': ['Master of Science'],
            'start_year': ['2020-03-16T00:00:00+01:00']
        }))

def test_process_data_person_8(create_table_mock,
                               setup_queue_event,
                               test_data):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['person_8']))

    handler(event, None)
    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'alias',
        pd.Series(['HELENG']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'name',
        pd.Series(['Helge Engen']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'experience',
        pd.Series([47]))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'examination_year',
        pd.Series(['1975']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'grade',
        pd.Series(['Master of Science']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'start_year',
        pd.Series(['2020-03-16T00:00:00+01:00']))

    create_table_mock.assert_table_data(
        'ubw_experience',
        pd.DataFrame({
            'alias': ['HELENG'],
            'name': ['Helge Engen'],
            'experience': [47],
            'examination_year': ['1975'],
            'grade': ['Master of Science'],
            'start_year': ['2020-03-16T00:00:00+01:00']
        }))

def test_process_data_person_9(create_table_mock,
                               setup_queue_event,
                               test_data):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['person_9']))

    handler(event, None)
    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'alias',
        pd.Series(['OLABER']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'name',
        pd.Series(['Ola Berge']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'experience',
        pd.Series([52]))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'examination_year',
        pd.Series(['1970']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'grade',
        pd.Series(['Master of Science']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'start_year',
        pd.Series(['2020-03-16T00:00:00+01:00']))

    create_table_mock.assert_table_data(
        'ubw_experience',
        pd.DataFrame({
            'alias': ['OLABER'],
            'name': ['Ola Berge'],
            'experience': [52],
            'examination_year': ['1970'],
            'grade': ['Master of Science'],
            'start_year': ['2020-03-16T00:00:00+01:00']
        }))

def test_process_data_person_10(create_table_mock,
                               setup_queue_event,
                               test_data):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['person_10']))

    handler(event, None)
    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'alias',
        pd.Series(['KNUAHM']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'name',
        pd.Series(['Knut Ahmed']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'experience',
        pd.Series([208]))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'examination_year',
        pd.Series(['1814']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'grade',
        pd.Series(['Master of Science']))

    create_table_mock.assert_table_data_column(
        'ubw_experience',
        'start_year',
        pd.Series(['2020-03-16T00:00:00+01:00']))

    create_table_mock.assert_table_data(
        'ubw_experience',
        pd.DataFrame({
            'alias': ['KNUAHM'],
            'name': ['Knut Ahmed'],
            'experience': [208],
            'examination_year': ['1814'],
            'grade': ['Master of Science'],
            'start_year': ['2020-03-16T00:00:00+01:00']
        }))

'''
def test_process_data_dataframe_content_person_1(
        create_table_mock,
        setup_queue_event,
        test_data):
    aliases = ['FREARN','EINHAL','SANAHM', 'CATKRI', 'TORAMU', 'CATMAD', 'DANBAK', 'HELENG', 'OLABER', 'KNUAHM']
    names = ['Fredrik Arnesen', 'Einar Halvorsen', 'Sander Ahmed', 'Cathrine Kristiansen', 'Tor Amundsen', 'Cathrine Madsen', 'Daniel Bakke', 'Helge Engen', 'Ola Berge', 'Knut Ahmed']
    experience = [32, 22, 12, 42, 37, 27, 17, 47, 52, 208]
    examination_year = ['1990', '2000', '2010', '1980', '1985', '1995', '2005', '1975', '1970', '1814']
    grade = ['Master of Science']
    start_year = ['2020-03-16T00:00:00+01:00']
    for i in range(0, 9):
        print("Alias: ", aliases[i])
        print("Name: ", names[i])
        print("Experience: ", experience[i])
        print("Examination year: ", examination_year[i])
        print("Data: ", test_data['person_'+str(i+1)])
        event = setup_queue_event(
            schema.Data(
                metadata=schema.Metadata(timestamp=1601294392),
                data=test_data['person_'+str(i+1)]))

        handler(event, None)

        create_table_mock.assert_table_data(
            'ubw_experience',
            pd.DataFrame({
                'alias': [aliases[i]],
                'name': [names[i]],
                'experience': [experience[i]],
                'examination_year': [examination_year[i]],
                'grade': [grade[0]],
                'start_year': [start_year[0]]
            }))
'''
'''
def test_process_data_dataframe_content_person_3(create_table_mock,
                                                 setup_queue_event,
                                                 test_data,
                                                 dynamodb_resource):
    event = setup_queue_event(
                schema.Data(
                    metadata=schema.Metadata(timestamp=1601294392),
                    data=test_data['person_3']))

    handler(event, None)

    create_table_mock.assert_table_data(
        'ubw_experience',
        pd.DataFrame({
            'alias': 'SANAHM',
            'name': 'Sander Ahmed',
            'experience': 12,
            'examination_year': '2010',
            'grade': ['Master of Science'],
            'start_year': ['2020-03-16T00:00:00+01:00']
        }))
'''
def test_process_only_appending_historical_data_person_1(
        s3_bucket,
        setup_queue_event,
        test_data,
        dynamodb_resource):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=1601294392),
            data=test_data['person_1']))

    handler(event, None)
    handler(event, None)

    keys_in_s3 = [x.key for x in s3_bucket.objects.all() if 'structured' in x.key]
    expected_keys = [
        'data/test/structured/ubw_experience/_common_metadata',
        'data/test/structured/ubw_experience/_metadata',
        'data/test/structured/ubw_experience/part.0.parquet',

    ]
    assert len(expected_keys) == len(keys_in_s3)
    assert all([keys_in_s3[i] == expected_keys[i] for i in range(len(keys_in_s3))])

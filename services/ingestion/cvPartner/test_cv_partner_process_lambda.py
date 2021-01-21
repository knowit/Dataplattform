from cv_partner_process_lambda import handler
from dataplattform.common import schema
from pytest import fixture
from os import path
from json import load
import pandas as pd


@fixture
def test_data():
    with open(path.join(path.dirname(__file__), 'test_data.json'), 'r') as json_file:
        yield load(json_file)


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


def test_initial_process(setup_queue_event, test_data, create_table_mock):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['data']))

    handler(event, None)
    create_table_mock.assert_table_created(
        'cv_partner_employees',
        'cv_partner_education',
        'cv_partner_blogs',
        'cv_partner_courses',
        'cv_partner_key_qualification',
        'cv_partner_languages',
        'cv_partner_project_experience',
        'cv_partner_technology_skills',
        'cv_partner_work_experience')


def test_process_table_content(setup_queue_event, test_data, create_table_mock):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['data']))

    handler(event, None)
    create_table_mock.assert_table_data_contains_df(
        'cv_partner_employees',
        pd.DataFrame({
            'user_id': ['user_id_1', 'user_id_2'],
            'default_cv_id': ['user_id_1_cv_id', 'user_id_2_cv_id'],
            'link': ["link1", "link2"],
            'navn': ['Test Testerson', 'Test Testerson 2'],
            'email': ["test@test.no", "test@test2.no"],
            'telefon': ['+123456', '+123456'],
            'born_year': [1995, 1985],
            'nationality': ["Norwegian", "Swedish"],
            'place_of_residence': ['Oslo', 'Oslo'],
            'cv_no_pdf': ["cv_no_pdf_key1", "cv_no_pdf_key2"],
            'cv_int_pdf': ["cv_int_pdf_key1", "cv_int_pdf_key2"],
            'cv_no_docx': ["cv_no_docx_key1", "cv_no_docx_key2"],
            'cv_int_docx': ["cv_int_docx_key1", "cv_int_docx_key2"],
            'image_key': ["image_key1", "image_key2"],
            'twitter': ["", "twitter2"]
        }))


def test_process_table_content_missing_born_date(setup_queue_event, test_data, create_table_mock):

    tmp_data = test_data['data']
    tmp_data[0]['cv'].pop('born_year', None)

    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=tmp_data))

    handler(event, None)
    create_table_mock.assert_table_data_contains_df(
        'cv_partner_employees',
        pd.DataFrame({
            'user_id': ['user_id_1', 'user_id_2'],
            'default_cv_id': ['user_id_1_cv_id', 'user_id_2_cv_id'],
            'link': ["link1", "link2"],
            'navn': ['Test Testerson', 'Test Testerson 2'],
            'email': ["test@test.no", "test@test2.no"],
            'telefon': ['+123456', '+123456'],
            'born_year': [-1, 1985],
            'nationality': ["Norwegian", "Swedish"],
            'place_of_residence': ['Oslo', 'Oslo'],
            'twitter': ["", "twitter2"]
        }))


def test_process_education_table_content(setup_queue_event, test_data, create_table_mock):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['data']))

    handler(event, None)
    create_table_mock.assert_table_data_contains_df(
        'cv_partner_education',
        pd.DataFrame({
            'user_id': ['user_id_1', 'user_id_1', 'user_id_2', 'user_id_2'],
            'degree': ['Bachelor1', 'Master1', 'Bachelor2', 'Master2'],
            'month_from': [8, 8, 8, 8],
            'month_to': [5, 6, 5, 6],
            'year_from': [2014, 2017, 2014, 2017],
            'year_to': [2019, 2019, 2019, 2019]
        }))


"""
Case: user1 has no education
"""


def test_process_education_table_content_missing(setup_queue_event, test_data,
                                                 create_table_mock):

    tmp_data = test_data['data']
    tmp_data[0]['cv'].pop('educations', None)

    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=tmp_data))

    handler(event, None)
    create_table_mock.assert_table_data_contains_df(
        'cv_partner_education',
        pd.DataFrame({
            'user_id': ['user_id_2', 'user_id_2'],
            'degree': ['Bachelor2', 'Master2'],
            'month_from': [8, 8],
            'month_to': [5, 6],
            'year_from': [2014, 2017],
            'year_to': [2019, 2019]
            }))


def test_project_experiences_df(setup_queue_event, test_data, create_table_mock):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['data']))

    handler(event, None)
    create_table_mock.assert_table_data_contains_df(
        'cv_partner_project_experience',
        pd.DataFrame({
            'user_id': ['user_id_1', 'user_id_1', 'user_id_2', 'user_id_2'],
            'customer': ['costumer1', 'costumer2', 'costumer3', 'Knowit Objectnet'],
            'month_from': [1, 6, 8, 12],
            'year_from': [2015, 2017, 2019, 2019],
            'project_experience_skills': ["HTML/CSS;Github", "Angular;npm", "Yarn;VS Code", "AWS DynamoDB;Github"],
            'roles': ["Fullstackutvikler",
                      "Frontendutvikler",
                      "Frontendutvikler;Brukeranalyse;DevOps-utvikler",
                      "Backendutvikler"]
            }))


"""
Case: project skills not defined for a project
"""


def test_project_experiences_df_project_skills_missing(setup_queue_event, test_data, create_table_mock):
    tmp_data = test_data['data']
    tmp_data[0]['cv']['project_experiences'][1].pop('project_experience_skills', None)

    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=tmp_data))

    handler(event, None)
    create_table_mock.assert_table_data_contains_df(
        'cv_partner_project_experience',
        pd.DataFrame({
            'user_id': ['user_id_1', 'user_id_1', 'user_id_2', 'user_id_2'],
            'customer': ['costumer1', 'costumer2', 'costumer3', 'Knowit Objectnet'],
            'month_from': [1, 6, 8, 12],
            'year_from': [2015, 2017, 2019, 2019],
            'project_experience_skills': ["HTML/CSS;Github", "", "Yarn;VS Code", "AWS DynamoDB;Github"],
            'roles': ["Fullstackutvikler",
                      "Frontendutvikler",
                      "Frontendutvikler;Brukeranalyse;DevOps-utvikler",
                      "Backendutvikler"]
            }))


"""
Case: costumer not defined for a project
"""


def test_project_experiences_df_costumer_missing(setup_queue_event, test_data, create_table_mock):
    tmp_data = test_data['data']
    tmp_data[0]['cv']['project_experiences'][0].pop('customer', None)

    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=tmp_data))

    handler(event, None)
    create_table_mock.assert_table_data_contains_df(
        'cv_partner_project_experience',
        pd.DataFrame({
            'user_id': ['user_id_1', 'user_id_1', 'user_id_2', 'user_id_2'],
            'customer': ["", 'costumer2', 'costumer3', 'Knowit Objectnet'],
            'month_from': [1, 6, 8, 12],
            'year_from': [2015, 2017, 2019, 2019],
            'project_experience_skills': ["HTML/CSS;Github", "Angular;npm", "Yarn;VS Code", "AWS DynamoDB;Github"],
            'roles': ["Fullstackutvikler",
                      "Frontendutvikler",
                      "Frontendutvikler;Brukeranalyse;DevOps-utvikler",
                      "Backendutvikler"]
            }))


"""
Test replace missing values with pd.NA
"""


def test_work_experiences_df_missing(setup_queue_event, test_data,
                                     create_table_mock):

    tmp_data = test_data['data']
    tmp_data[1]['cv']['work_experiences'][0].pop('month_from', None)

    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=tmp_data))

    exp_df = pd.DataFrame({
            'user_id': ['user_id_1', 'user_id_1', 'user_id_1', 'user_id_2', 'user_id_2', 'user_id_2'],
            'month_from': [6, 6, 8, -1, 6, 8]
            })

    handler(event, None)
    create_table_mock.assert_table_data_contains_df(
        'cv_partner_work_experience', exp_df
        )


"""
Test replace none values with empty string
"""


def test_tag_value_none(setup_queue_event, test_data,
                        create_table_mock):

    tmp_data = test_data['data']
    print(tmp_data[1]['cv']['technologies'][0]['technology_skills'][0]['tags'])
    tmp_data[1]['cv']['technologies'][0]['technology_skills'][0]['tags']['no'] = None

    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=tmp_data))

    handler(event, None)

    create_table_mock.assert_table_data(
        'cv_partner_technology_skills',
        pd.DataFrame({
            'user_id': ['user_id_1', 'user_id_1', 'user_id_1', 'user_id_2', 'user_id_2'],
            'category': ["", "Programmeringsspråk", "Webutvikling", "Object-Relational Mapping (ORM)",
                         "Systemutvikling"],
            'technology_skills': ["", "Java", "Angular;HTML", ";Hibernate", "Android Studio"],
        }))

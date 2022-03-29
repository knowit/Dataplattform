from cvpartner.cv_partner_process_lambda import handler
from dataplattform.common import schema
from pytest import fixture
from os import path
from json import load
import pandas as pd
from io import BytesIO

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


def test_initial_process(setup_queue_event, test_data, create_table_mock, dynamodb_resource):
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


def test_process_table_content(setup_queue_event, test_data, create_table_mock, dynamodb_resource):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['data']))

    handler(event, None)
    create_table_mock.assert_table_data_contains_df(
        'cv_partner_employees',
        pd.DataFrame({
            'user_id': ['60cc81232e97ff100ca405c6', '60cc7fce68679f0fc4336177'],
            'guid': ['5d79f8b771cd4921b667f9227aece292213806d6', 'b051b402346144a6cdcceb0027f6e80d29019f50'],
            'default_cv_id': ['60cc81232e97ff100ca405c7', '60cc7fce68679f0fc4336178'],
            'link': ['link1', 'link2'],
            'twitter': ['', ''],
            'email': ['einar.halvorsen@knowit.no', 'fredrik.arnesen@knowit.no'],
            'navn': ['Einar Halvorsen', 'Fredrik Arnesen'],
            'telefon': ['12345678', '87654321'],
            'born_year': [1975, 1995],
            'nationality': ["Norwegian", "Norwegian"],
            'place_of_residence': ['', 'Sandvika'],
            'title': ['Systemkonsulent', 'Utvikler'],
            'image_key': ["public/images/dad875c3-c3d0-47da-b6b9-4c605a803f78.jpg",
                          "public/images/ac28979d-9694-4537-a299-bf713d1aef79.jpg"]
        }))


def test_process_table_content_missing_born_date(setup_queue_event, test_data, create_table_mock, dynamodb_resource):

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
            'user_id': ['60cc81232e97ff100ca405c6', '60cc7fce68679f0fc4336177'],
            'guid': ['5d79f8b771cd4921b667f9227aece292213806d6', 'b051b402346144a6cdcceb0027f6e80d29019f50'],
            'default_cv_id': ['60cc81232e97ff100ca405c7', '60cc7fce68679f0fc4336178'],
            'link': ['link1', 'link2'],
            'navn': ['Einar Halvorsen', 'Fredrik Arnesen'],
            'email': ['einar.halvorsen@knowit.no', 'fredrik.arnesen@knowit.no'],
            'telefon': ['12345678', '87654321'],
            'born_year': [-1, 1995],
            'nationality': ["Norwegian", "Norwegian"],
            'place_of_residence': ['', 'Sandvika'],
            'twitter': ['', '']
        }))


def test_process_education_table_content(setup_queue_event, test_data, create_table_mock, dynamodb_resource):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['data']))

    handler(event, None)
    create_table_mock.assert_table_data_contains_df(
        'cv_partner_education',
        pd.DataFrame({
            'user_id': ['60cc81232e97ff100ca405c6', '60cc81232e97ff100ca405c6',
                        '60cc7fce68679f0fc4336177', '60cc7fce68679f0fc4336177'],
            'degree': ['Bachelor', 'Master', 'Bachelor', 'Master'],
            'description': ['Informatikk', 'Informatikk: Kunstig Intelligens',
                            'Informatikk: Digital Økonomi og Ledelse', 'Informatikk: Digital Økonomi og Ledelse'],
            'month_from': [8, 8, 8, 8],
            'month_to': [7, 6, 6, 6],
            'school': ['NTNU', 'NTNU', 'Universitetet i Oslo', 'Universitetet i Oslo'],
            'year_from': [2012, 2015, 2015, 2018],
            'year_to': [2015, 2017, 2018, 2020]
        }))


"""
Case: user1 has no education
"""


def test_process_education_table_content_missing(setup_queue_event, test_data,
                                                 create_table_mock, dynamodb_resource):

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
            'user_id': ['60cc7fce68679f0fc4336177', '60cc7fce68679f0fc4336177'],
            'degree': ['Bachelor', 'Master'],
            'description': ['Informatikk: Digital Økonomi og Ledelse', 'Informatikk: Digital Økonomi og Ledelse'],
            'month_from': [8, 8],
            'month_to': [6, 6],
            'school': ['Universitetet i Oslo', 'Universitetet i Oslo'],
            'year_from': [2015, 2018],
            'year_to': [2018, 2020]
            }))


"""
Case: user1 has no courses, api reports cv.courses = [], while for user2 the cv.courses entry is not present,
therefore the data frame should not be made
"""


def test_process_courses_table_content_empty(setup_queue_event, test_data,
                                                 create_table_mock, dynamodb_resource):

    tmp_data = test_data['data']
    tmp_data[0]['cv']['courses'] = []

    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=tmp_data))

    handler(event, None)

    create_table_mock.assert_table_created(
        'cv_partner_employees',
        'cv_partner_education',
        'cv_partner_blogs',
        'cv_partner_key_qualification',
        'cv_partner_languages',
        'cv_partner_project_experience',
        'cv_partner_technology_skills',
        'cv_partner_work_experience')


def test_project_experiences_df(setup_queue_event, test_data, create_table_mock, dynamodb_resource):
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['data']))

    handler(event, None)
    create_table_mock.assert_table_data_contains_df(
        'cv_partner_project_experience',
        pd.DataFrame({
            'user_id': ['60cc81232e97ff100ca405c6', '60cc7fce68679f0fc4336177'],
            'customer': ['Eksempelkunde 1', 'Eksempelkunde 2'],
            'month_from': [1, 8],
            'year_from': [2015, 2019],
            'project_experience_skills': ["aws;smidig utvikling;fullstack", "serverless;azure;svelte"],
            'roles': ["Teamlead;Scrum master",
                      "Utvikler"]
            }))


"""
Case: project skills not defined for a project
"""


def test_project_experiences_df_project_skills_missing(setup_queue_event, test_data, create_table_mock,
                                                       dynamodb_resource):
    tmp_data = test_data['data']
    tmp_data[0]['cv']['project_experiences'][0].pop('project_experience_skills', None)

    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=tmp_data))

    handler(event, None)
    create_table_mock.assert_table_data_contains_df(
        'cv_partner_project_experience',
        pd.DataFrame({
            'user_id': ['60cc81232e97ff100ca405c6', '60cc7fce68679f0fc4336177'],
            'customer': ['Eksempelkunde 1', 'Eksempelkunde 2'],
            'month_from': [1, 8],
            'year_from': [2015, 2019],
            'project_experience_skills': ["", "serverless;azure;svelte"],
            'roles': ["Teamlead;Scrum master",
                      "Utvikler"]
            }))


"""
Case: costumer not defined for a project
"""


def test_project_experiences_df_costumer_missing(setup_queue_event, test_data, create_table_mock, dynamodb_resource):
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
            'user_id': ['60cc81232e97ff100ca405c6', '60cc7fce68679f0fc4336177'],
            'customer': ['', 'Eksempelkunde 2'],
            'month_from': [1, 8],
            'year_from': [2015, 2019],
            'project_experience_skills': ["aws;smidig utvikling;fullstack", "serverless;azure;svelte"],
            'roles': ["Teamlead;Scrum master",
                      "Utvikler"]
            }))


"""
Test replace missing values with pd.NA
"""


def test_work_experiences_df_missing(setup_queue_event, test_data,
                                     create_table_mock, dynamodb_resource):

    tmp_data = test_data['data']
    tmp_data[0]['cv']['work_experiences'][1].pop('month_from', None)

    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=tmp_data))

    exp_df = pd.DataFrame({
            'user_id': ['60cc81232e97ff100ca405c6', '60cc81232e97ff100ca405c6', '60cc7fce68679f0fc4336177'],
            'month_from': [6, -1, 11]
            })

    handler(event, None)
    create_table_mock.assert_table_data_contains_df(
        'cv_partner_work_experience', exp_df
        )


"""
Test replace none values with empty string
"""


def test_tag_value_none(setup_queue_event, test_data,
                        create_table_mock, dynamodb_resource):

    tmp_data = test_data['data']
    tmp_data[1]['cv']['technologies'][0]['technology_skills'][0]['tags']['no'] = None

    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=tmp_data))

    handler(event, None)

    create_table_mock.assert_table_data(
        'cv_partner_technology_skills',
        pd.DataFrame({
            'user_id': ['60cc81232e97ff100ca405c6', '60cc81232e97ff100ca405c6',
                        '60cc81232e97ff100ca405c6', '60cc7fce68679f0fc4336177'],
            'category': ["", "Smidig utvikling", "Skytjenester", ""],
            'technology_skills': ["", "Scrum", "AWS;Microsoft Azure", ";azure;svelte;Java"]
        }))


def test_tag_value_none_2(setup_queue_event, test_data,
                        create_table_mock, dynamodb_resource):

    tmp_data = test_data['data']
    tmp_data[1]['cv']['technologies'][0]['technology_skills'][0]['tags'] = None

    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=tmp_data))

    handler(event, None)

    create_table_mock.assert_table_data(
        'cv_partner_technology_skills',
        pd.DataFrame({
            'user_id': ['60cc81232e97ff100ca405c6', '60cc81232e97ff100ca405c6',
                        '60cc81232e97ff100ca405c6', '60cc7fce68679f0fc4336177'],
            'category': ["", "Smidig utvikling", "Skytjenester", ""],
            'technology_skills': ["", "Scrum", "AWS;Microsoft Azure", ";azure;svelte;Java"]
        }))


def test_set_guid_from_ad_data(s3_bucket, setup_queue_event, test_data, dynamodb_resource):
    tmp_data = test_data['data']
    tmp_data[1]['cv']['email'] = "non.existing@mail.no"
    event = setup_queue_event(
        schema.Data(
            metadata=schema.Metadata(timestamp=0),
            data=test_data['data']))

    handler(event, None)

    cv_partner_employees_object = s3_bucket.Object("data/test/structured/cv_partner_employees/part.0.parquet")
    cv_partner_employees = pd.read_parquet(BytesIO(cv_partner_employees_object.get()['Body'].read()))
    assert cv_partner_employees.loc[cv_partner_employees['user_id'] == "60cc81232e97ff100ca405c6"]['guid'][0] \
           == "5d79f8b771cd4921b667f9227aece292213806d6"
    assert len(cv_partner_employees) == 1

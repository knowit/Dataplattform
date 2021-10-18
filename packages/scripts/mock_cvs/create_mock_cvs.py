"""
This script generates fake CVs and POSTs them to CvPartner test-api.
Only intended to run once.
"""
from faker import Faker
import requests
import boto3
import random
import datetime
import time

fake = Faker('no_NO')
dynamodb_client = boto3.client('dynamodb')
ssm_client = boto3.client('ssm')

ssm_path = '/dev/cvPartnerPoller'
api_url = ssm_client.get_parameter(Name=f'{ssm_path}/cv_partner_url')['Parameter']['Value']
api_token = ssm_client.get_parameter(Name=f'{ssm_path}/cv_partner_api_token',
                                     WithDecryption=True)['Parameter']['Value']
office_id = ssm_client.get_parameter(Name=f'{ssm_path}/cv_partner_objectnet_id')['Parameter']['Value']
country_id = ssm_client.get_parameter(Name=f'{ssm_path}/cv_partner_country_id')['Parameter']['Value']


SAMPLE_EDUCATIONS = [
    {
        'degree': {'no': 'Bachelor', 'int': 'Bachelor'},
        'description': {
            'no': 'Informatikk: programmering og systemarkitektur',
            'int': 'Informatics: Programming and System Architecture'
        },
        'school': {
            'no': 'Universitetet i Oslo',
            'int': 'University of Oslo'
        }
    },
    {
        'degree': {'no': 'Master', 'int': 'Master'},
        'description': {
            'no': 'Kommunikasjonsteknologi og digital sikkerhet',
            'int': 'Communication Technology and Digital Security'
        },
        'school': {
            'no': 'Norges teknisk-naturvitenskapelige universitet',
            'int': 'Norwegian University of Science and Technology'
        }
    }]

SAMPLE_ROLES = [
    {
        'name': {'no': 'Fullstackutvikler'},
        'long_description': {'no': fake.text()}
    },
    {
        'name': {'no': 'Teamlead'},
        'long_description': {'no': fake.text()}
    },
    {
        'name': {'no': 'Frontendutvikler'},
        'long_description': {'no': fake.text()}
    }
]


SAMPLE_SKILLS = ['Java', 'Kotlin', 'Python', 'JavaScript', 'React', 'AWS Lambda', 'Git', 'Node.js', 'JSON', 'Vue.js',
                 'GitHub', 'Jenkins', 'Oracle']


def user_payload(user, date_of_birth):
    return {
        'user': {
            'country_id': country_id,
            'email': user['email']['S'],
            'external_unique_id': user['guid']['S'],
            'office_id': office_id,
            'role': 'consultant',
            'name': user['displayName']['S'],
            'telephone': fake.phone_number(),
            'born_day': date_of_birth.day,
            'born_month': date_of_birth.month,
            'born_year': date_of_birth.year,
            'title': {'no': 'Systemkonsulent', 'int': 'Systems consultant'},
            'nationality': {'no': 'Norsk', 'int': 'Norwegian'},
            'place_of_residence': {'no': 'Oslo', 'int': 'Oslo'}
        }
    }


def education_payload(date_of_birth):
    education = random.choice(SAMPLE_EDUCATIONS)
    year_from = date_of_birth.year + 18
    year_to = year_from + 3 if education['degree']['no'] == 'Bachelor' else year_from + 5

    return {
        'education': {
            'degree': education['degree'],
            'description': education['description'],
            'school': education['school'],
            'month_from': '8',
            'month_to': '6',
            'year_from': str(year_from),
            'year_to': str(year_to)
        }
    }


def work_experience_payload(education_finished_year):
    current_year = datetime.datetime.now().year
    years_of_work_experience = current_year - education_finished_year
    payloads = [{
        'work_experience': {
            'employer': {'no': 'Knowit Objectnet'},
            'description': {'no': 'Fullstackutvikler', 'int': 'Full stack developer'},
            'long_description': {'no': fake.text()},
            'month_from': '8',
            'year_from': str(current_year - 2),
            'year_to': ''
        }
    }]

    if years_of_work_experience == 4:
        payloads.append({
            'work_experience': {
                'employer': {'no': fake.company()},
                'description': {'no': 'Fullstackutvikler', 'int': 'Full stack developer'},
                'long_description': {'no': fake.text()},
                'month_from': '8',
                'month_to': '8',
                'year_from': str(current_year - years_of_work_experience),
                'year_to': str(str(current_year - 2))
            }
        })

    return payloads


def project_experience_payload():
    current_year = datetime.datetime.now().year

    return {
        'project_experience': {
            'industry': {'no': 'Annet'},
            'customer': {'no': fake.company()},
            'description': {'no': fake.bs().capitalize()},
            'long_description': {'no': fake.text()},
            'year_from': str(current_year - 2),
            'year_to': str(current_year)
        }
    }


def skill_payload(skill_type, skill):
    return {
        skill_type: {
            'tags': {
                'no': skill
            }
        }
    }


def initialize_user(user, headers):
    birth_date = fake.date_of_birth(minimum_age=25, maximum_age=25)
    response = requests.post(f'{api_url}/v1/users',
                             headers=headers, json=user_payload(user, birth_date))
    return response.json()['user_id'], response.json()['default_cv_id']


def add_user_education(birth_date, headers, user_id, cv_id):
    payload = education_payload(birth_date)
    response = requests.post(f'{api_url}/v3/cvs/{user_id}/{cv_id}/educations',
                             headers=headers, json=payload)
    return int(payload['education']['year_to'])


def add_work_experience(graduation_year, headers, user_id, cv_id):
    payloads = work_experience_payload(graduation_year)
    return [requests.post(f'{api_url}/v3/cvs/{user_id}/{cv_id}/work_experiences',
                          headers=headers, json=payload) for payload in payloads]


def add_project_experience(headers, user_id, cv_id):
    payload = project_experience_payload()
    response = requests.post(f'{api_url}/v3/cvs/{user_id}/{cv_id}/project_experiences',
                             headers=headers, json=payload)
    return response.json()['_id']


def add_project_role(headers, user_id, cv_id, project_experience_id):
    payload = {
        'role': random.choice(SAMPLE_ROLES)
    }
    return requests.post(f'{api_url}/v3/cvs/{user_id}/{cv_id}/project_experiences/{project_experience_id}/roles',
                         headers=headers, json=payload)


def add_technology_category(headers, user_id, cv_id, category):
    payload = {
        'technology': {
            'category': {'no': category}
        }
    }
    response = requests.post(f'{api_url}/v3/cvs/{user_id}/{cv_id}/technologies',
                             headers=headers, json=payload)
    return response.json()['_id']


def add_skills(headers, user_id, cv_id, project_experience_id, technology_category_id):
    skills = random.sample(SAMPLE_SKILLS, 5)
    for skill in skills:
        requests.post(
            f'{api_url}/v3/cvs/{user_id}/{cv_id}/project_experiences/{project_experience_id}/project_experience_skills',
            headers=headers, json=skill_payload('project_experience_skill', skill))

        requests.post(f'{api_url}/v3/cvs/{user_id}/{cv_id}/technologies/{technology_category_id}/technology_skills',
                      headers=headers, json=skill_payload('technology_skill', skill))

        time.sleep(1)


def main():
    response = dynamodb_client.scan(TableName='dev_personal_metadata_table')
    users = response['Items']

    headers = {'Authorization': f'Bearer {api_token}', 'Content-type': 'application/json'}

    for user in users:
        birth_date = fake.date_of_birth(minimum_age=25, maximum_age=25)
        user_id, cv_id = initialize_user(user, headers)
        graduation_year = add_user_education(birth_date, headers, user_id, cv_id)
        add_work_experience(graduation_year, headers, user_id, cv_id)

        time.sleep(1)

        project_experience_id = add_project_experience(headers, user_id, cv_id)
        add_project_role(headers, user_id, cv_id, project_experience_id)
        technology_category_id = add_technology_category(headers, user_id, cv_id, 'Systemutvikling')

        time.sleep(1)

        add_skills(headers, user_id, cv_id, project_experience_id, technology_category_id)

        time.sleep(55)


if __name__ == '__main__':
    main()

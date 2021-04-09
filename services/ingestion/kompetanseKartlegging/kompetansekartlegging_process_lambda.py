from dataplattform.common.handlers.process import PersonDataProcessHandler
from dataplattform.common.repositories.person_repository import PersonIdentifierType
from typing import Dict
import pandas as pd

handler = PersonDataProcessHandler(PersonIdentifierType.EMAIL)


@handler.process(partitions={}, person_data_tables=['kompetansekartlegging_users', 'kompetansekartlegging_answers'])
def process(data, events) -> Dict[str, pd.DataFrame]:
    data = data[0].json()['data']

    def create_user_df():
        users = [{'username': user["username"], 'email': user['attributes'][0]['Value']}
                 for user in data['users']]
        return pd.DataFrame(data=users)

    def create_answers_df():
        answer_data = data['answers']
        formatted_answer_data = []

        for entry in answer_data:
            email = entry['email']
            answers = filter(lambda answer: 'unanswered' not in answer, entry['answers'])
            formatted_answer_data.append(
                list(map(
                    lambda answer: {
                        'email': email,
                        'question_id': answer['question']['id'],
                        'knowledge': answer.get('knowledge'),
                        'motivation': answer.get('motivation'),
                        'customScaleValue': answer.get('customScaleValue'),
                    }, answers)
                )
            )

        flattened = [data_point for sublist in formatted_answer_data for data_point in sublist]
        return pd.DataFrame(data=flattened)

    def create_answers_alt():
        return pd.json_normalize(data['answers'])

    def create_catalogs_df():
        return pd.DataFrame(data['catalogs'])

    def create_questions_df():
        return pd.DataFrame(data['questions'])

    def create_categories_df():
        return pd.DataFrame(data['categories'])

    return {
        'kompetansekartlegging_users': create_user_df(),
        'kompetansekartlegging_answers': create_answers_df(),
        'kompetansekartlegging_catalogs': create_catalogs_df(),
        'kompetansekartlegging_questions': create_questions_df(),
        'kompetansekartlegging_categories': create_categories_df(),
        'alternative_answers': create_answers_alt()
    }

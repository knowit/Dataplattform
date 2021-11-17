from dataplattform.common.handlers.process import PersonDataProcessHandler
from dataplattform.common.repositories.person_repository import PersonIdentifierType
from typing import Dict
import pandas as pd

handler = PersonDataProcessHandler(PersonIdentifierType.EMAIL)


@handler.process(partitions={}, overwrite=True, overwrite_all_versions=True,
                 person_data_tables=['kompetansekartlegging_users', 'kompetansekartlegging_answers'])
def process(data, events) -> Dict[str, pd.DataFrame]:
    data = data[0].json()['data']

    def create_users_df():
        df = pd.json_normalize(data['users'], meta=['username'], record_path=['attributes'])
        df.rename(columns={'Value': 'email'}, inplace=True)
        fields = ['username', 'email']
        return df[fields]

    def create_answers_df():
        df = pd.json_normalize(data['answers'], meta=['username', 'email'], record_path=['answers'])
        df.rename(columns={'question.id': 'questionId'}, inplace=True)
        fields = ['username', 'email', 'questionId', 'knowledge', 'motivation', 'updatedAt', 'customScaleValue']
        return df[fields]

    def create_catalogs_df():
        return pd.DataFrame(data['catalogs'])

    def create_questions_df():
        return pd.DataFrame(data['questions'])

    def create_categories_df():
        return pd.DataFrame(data['categories'])

    return {
        'kompetansekartlegging_users': create_users_df(),
        'kompetansekartlegging_answers': create_answers_df(),
        'kompetansekartlegging_catalogs': create_catalogs_df(),
        'kompetansekartlegging_questions': create_questions_df(),
        'kompetansekartlegging_categories': create_categories_df()
    }

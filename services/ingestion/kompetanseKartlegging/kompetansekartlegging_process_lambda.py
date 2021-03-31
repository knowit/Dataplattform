from dataplattform.common.handlers.process import PersonDataProcessHandler
from dataplattform.common.repositories.person_repository import PersonIdentifierType
from typing import Dict
import pandas as pd
import numpy as np

handler = PersonDataProcessHandler(PersonIdentifierType.EMAIL)


@handler.process(partitions={}, person_data_tables=['kompetansekartlegging_employees', 'kompetansekartlegging_answers'])
def process(data, events) -> Dict[str, pd.DataFrame]:
    data = data[0].json()['data']

    def none_to_empty_str(tmp_str):
        if tmp_str is None:
            return ''
        else:
            return str(tmp_str)

    """
    Workaround for known pandas issue with conversion to int in
    the presence of nullable integers.
    """
    def column_type_to_int(col):
        col = pd.to_numeric(col, errors='coerce')
        col = col.fillna(value=-1)
        col = col.astype(dtype='int32')
        return col

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
                    lambda a: {
                        'email': email,
                        'question_id': a['question']['id'],
                        'knowledge': a.get('knowledge'),
                        'motivation': a.get('motivation'),
                        'customScaleValue': a.get('customScaleValue'),
                    }, answers)
                )
            )

        flattened = [data_point for sublist in formatted_answer_data for data_point in sublist]
        return pd.DataFrame(data=flattened)



    # def create_education_df(df):
    #     education_df_coloums = ['user_id', 'degree', 'description', 'month_from',
    #                             'month_to', 'school', 'year_from', 'year_to']
    #     edu_normalizable_cols = ['degree', 'description', 'school']
    #     tmp = create_df(df, 'educations', education_df_coloums, edu_normalizable_cols)
    #     tmp['month_to'] = column_type_to_int(tmp['month_to'])
    #     tmp['year_to'] = column_type_to_int(tmp['year_to'])
    #     tmp['month_from'] = column_type_to_int(tmp['month_from'])
    #     tmp['year_from'] = column_type_to_int(tmp['year_from'])

    #     return tmp

    return {
        'kompetansekartlegging_employees': create_user_df(),
        'kompetansekartlegging_answers': create_answers_df()
    }

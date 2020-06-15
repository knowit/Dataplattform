from dataplattform.common.handler import Handler
from dataplattform.common.schema import Data, Metadata
from datetime import datetime
import pandas as pd
import json
import numpy as np
from typing import Dict
import re
from collections import defaultdict
from dateutil.parser import isoparse

handler = Handler()


@handler.ingest()
def ingest(event) -> Data:

    event_body = event['body']
    body_json = json.loads(event_body)

    return Data(
        Metadata(timestamp=int(datetime.now().timestamp())),
        data=body_json
    )


@handler.process(partitions={})
def process(data) -> Dict[str, pd.DataFrame]:

    def make_dataframes(d):
        d = d.json()
        metadata, payload = d['metadata'], d['data']
        user = payload.get('user', 'undefined')

        form_name = payload['tableName']
        form_name.replace(',', '_')
        form_name = user + '_' + form_name  # avoid overwrite
        form_name = re.sub('[^A-Za-z0-9]+', '_', form_name)
        questions_form_name = form_name + '_' + 'questions'

        special_questions_list = ['GRID', 'CHECKBOX_GRID']
        other_questions_list = ['MULTIPLE_CHOICE', 'CHECKBOX', 'LIST', 'FILE_UPLOAD', 'TEXT', 'PARAGRAPH_TEXT', 'DATE', 'TIME', 'SCALE']

        responses = payload.get('responses', None)  # list

        def create_questions_dataframe(responses):

            def create_individual_question_dataframe(question, responder):
                question_data = {}
                question_data['question_title'] = question['title']
                question_data['type'] = question['type']
                question_data['helpText'] = question['helpText']
                question_data['responder'] = responder

                sub_question_list = []
                sub_answers_list = []

                new_sub_questions_list = []
                new_sub_answers_list = []

                if question_data['type'] in special_questions_list:
                    sub_question_list = question['typeData']['rows']
                    tmp_answers_list = question['answer']
                    if (tmp_answers_list is not None):
                        sub_answers_list = tmp_answers_list['response']
                    
                    i = 0
                    for elem in sub_answers_list:
                        if type(elem) == list:
                            for sub_elem in elem:
                                new_sub_questions_list.append(sub_question_list[i])
                                new_sub_answers_list.append(sub_elem)
                        i = i + 1

                elif question_data['type'] in other_questions_list:
                    tmp_answers_list = question['answer']
                    if (tmp_answers_list is not None):
                        sub_answers_list = tmp_answers_list['response']
                    if (type(sub_answers_list) == str):
                        sub_answers_list = [sub_answers_list]
                    new_sub_answers_list = sub_answers_list
                    new_sub_questions_list = ['']*len(new_sub_answers_list)

                questions_list = [[*question_data.values(), sub_q, sub_a] for (sub_q, sub_a) in zip(new_sub_questions_list, new_sub_answers_list)]
                questions_dataframe_coloumns = [*question_data.keys()]
                questions_dataframe_coloumns.append('Subquestions title')
                questions_dataframe_coloumns.append('Answer')

                return pd.DataFrame(questions_list, columns=questions_dataframe_coloumns)
                
            result_frame = pd.DataFrame()
            for repsons in responses:
                questions = repsons['questions']
                responder = repsons['id']
                ind_dfs = [create_individual_question_dataframe(question, responder) for question in questions]
                result_frame = pd.concat(ind_dfs, ignore_index=True)
            print("")
            print(result_frame)
            return result_frame
        
        questions_dataframe = create_questions_dataframe(responses)
        metadata_df = pd.DataFrame({'uploaded_by_user': user,
                                    'time_added': [metadata['timestamp']]})
        return questions_form_name, questions_dataframe, metadata_df

    question_tables, metadata_tables = list(zip(*[
        (
            (q_form_name, questions_df),
            metadata_df
        ) for q_form_name, questions_df, metadata_df in [make_dataframes(d) for d in data]
    ]))

    return {
            **dict(question_tables),
            'google_forms_metadata': pd.concat(metadata_tables)
    }

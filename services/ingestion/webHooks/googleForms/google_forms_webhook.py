from dataplattform.common.handler import Handler
from dataplattform.common.schema import Data, Metadata
from datetime import datetime
import pandas as pd
import json
from typing import Dict
import re
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


@handler.process(partitions={'google_forms_data': ['form_name', 'uploaded_by_user']})
def process(data) -> Dict[str, pd.DataFrame]:

    def make_dataframes(d):
        d = d.json()
        metadata, payload = d['metadata'], d['data']
        user = payload.get('user', 'undefined')

        form_name = payload['tableName']
        form_name.replace(',', '_')
        form_name = re.sub('[^A-Za-z0-9]+', '_', form_name)

        special_questions_list = ['GRID', 'CHECKBOX_GRID']
        multiple_choice = ['MULTIPLE_CHOICE', 'CHECKBOX', 'LIST']
        other_questions_list = ['FILE_UPLOAD',
                                'TEXT', 'PARAGRAPH_TEXT', 'DATE', 'TIME', 'SCALE']

        def to_timestamp(date):
            return int(isoparse(date).timestamp()) if isinstance(date, str) else int(date)

        def create_questions_dataframe(responses):

            def create_individual_dataframe(question, responder, timestamp, isQuiz):
                data = {'question_title': question['title'],
                        'type': question['type'],
                        'help_text': question['helpText'],
                        'responder': responder,
                        'timestamp': to_timestamp(timestamp),
                        'is_quiz': isQuiz
                        }

                new_sub_questions_list = []
                new_sub_answers_list = []
                answer_check_list = []

                def get_response(question):
                    tmp_answers_list = question['answer']
                    sub_answers_list = ['']
                    if (tmp_answers_list is not None):
                        sub_answers_list = tmp_answers_list['response']
                    return sub_answers_list

                def string_to_list(sub_answers):
                    return [sub_answers] if not isinstance(sub_answers, list) else sub_answers

                question_type = data['type']

                if question_type in special_questions_list:
                    sub_question_list = question['typeData']['rows']
                    sub_answers_list = get_response(question)
                    for i, elem in enumerate(sub_answers_list):  # list of lists
                        if isinstance(elem, list):
                            for sub_elem in elem:
                                new_sub_questions_list.append(sub_question_list[i])
                                new_sub_answers_list.append(sub_elem)
                        else:
                            new_sub_questions_list.append(sub_question_list[i])
                            new_sub_answers_list.append(elem)

                elif question_type in other_questions_list:
                    new_sub_answers_list = string_to_list(get_response(question))
                    new_sub_questions_list = ['']*len(new_sub_answers_list)
                elif question_type in multiple_choice:
                    new_sub_answers_list = string_to_list(get_response(question))
                    new_sub_questions_list = ['']*len(new_sub_answers_list)
                    if (isQuiz):
                        choices = question['typeData']['choices']
                        c_keys = [choice['value'] for choice in choices]
                        c_values = [choice['isCorrect'] for choice in choices]
                        d = dict(zip(c_keys, c_values))
                        answer_check_list = [d.get(elem, pd.NA) for elem in new_sub_answers_list]
                else:
                    raise KeyError('Question type: ' + question_type + ' is not supported')

                if (len(answer_check_list) == 0):
                    answer_check_list = [pd.NA]*len(new_sub_answers_list)

                f_c = question['typeData'].get('feedbackCorrect', '')
                f_ic = question['typeData'].get('feedbackIncorrect', '')

                feedback_correct = [f_c]*len(new_sub_answers_list)
                feedback_incorrect = [f_ic]*len(new_sub_answers_list)

                points = question['typeData'].get('points', 0)
                points_list = [0]*len(new_sub_answers_list)
                points_list[0] = points

                zipped_list = zip(new_sub_questions_list,
                                  new_sub_answers_list,
                                  answer_check_list,
                                  feedback_correct,
                                  feedback_incorrect,
                                  points_list)

                questions_list = [[*data.values(), *vals] for vals in zipped_list]
                df_columns = [*data.keys(), 'sub_question text', 'answer',
                              'is_correct', 'feedback_correct', 'feedback_incorrect',
                              'available_points']

                return pd.DataFrame(questions_list, columns=df_columns)

            result_frame_list = []
            for repsons in responses:
                ind_dfs = [create_individual_dataframe(q, repsons['id'],
                                                       repsons['timestamp'],
                                                       repsons['isQuiz']) for q in repsons['questions']]

                result_frame_list.append(pd.concat(ind_dfs, ignore_index=True))

            result_frame = pd.concat(result_frame_list, ignore_index=True)
            result_frame['form_name'] = pd.Series([form_name]*result_frame.shape[0], index=result_frame.index)
            result_frame['uploaded_by_user'] = pd.Series([user]*result_frame.shape[0], index=result_frame.index)
            result_frame['time_uploaded'] = pd.Series([metadata['timestamp']]*result_frame.shape[0],
                                                      index=result_frame.index)

            return result_frame

        responses = payload.get('responses')
        questions_dataframe = pd.DataFrame()
        if len(responses) > 0:
            questions_dataframe = create_questions_dataframe(responses)

        return questions_dataframe

    question_tables = [make_dataframes(d) for d in data]

    return {
            'google_forms_data': pd.concat(question_tables)
    }

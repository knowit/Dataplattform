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

        form_name = payload['formName']
        form_name = user + '-' + form_name  # avoid overwrite
        form_name = re.sub('[^A-Za-z0-9]+', '_', form_name)
        questions_form_name = form_name + '_' + 'questions'
        answers_form_name = form_name + '_' + 'answers'
        
        def to_timestamp(date):
            return int(isoparse(date).timestamp()) if isinstance(date, str) else int(date)

        responses = payload.get('responses', None)  # list

        def create_questions_dataframe(responses):
            questions_dict = {}

            for repsons in responses:
                answers = repsons['answers']
                for answer in answers:
                    questions_dict[answer['questionId']] = answer['questionsTitle']

            questions_dataframe = pd.DataFrame({'question id': list(questions_dict.keys()),
                                                'question title': list(questions_dict.values())})

            respondents = []
            for repsons in responses:
                respondents_answers = defaultdict(list, {k: [] for k in questions_dict.keys()})
                respondents_answers['respondent'] = repsons['respondent']
                respondents_answers['timestamp'] = to_timestamp(repsons['timestamp'])
                answers = repsons['answers']
                for answer in answers:
                    respondents_answers[answer['questionId']] = answer['response']
                respondents.append(respondents_answers)

            answers_dataframe = pd.DataFrame(r for r in respondents)
            return questions_dataframe, answers_dataframe

        questions_dataframe, answers_dataframe = create_questions_dataframe(responses)
        metadata_df = pd.DataFrame({'uploaded_by_user': user,
                                    'time_added': [metadata['timestamp']]})
        return questions_form_name, questions_dataframe, answers_form_name, answers_dataframe, metadata_df

    question_tables, answers_tables, metadata_tables = list(zip(*[
        (
            (q_form_name, questions_df),
            (a_form_name, answers_df),
            metadata_df
        ) for q_form_name, questions_df, a_form_name, answers_df, metadata_df in [make_dataframes(d) for d in data]
    ]))

    return {
            **dict(question_tables),
            **dict(answers_tables),
            'google_forms_metadata': pd.concat(metadata_tables)
    }

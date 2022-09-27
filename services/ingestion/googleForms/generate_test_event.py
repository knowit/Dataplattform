import json
with open('tests/test_data_files/test_data_quiz_single_respondent_valid_types.json') as f:
    body = json.load(f)

data = {
    'body': json.dumps(body)
}

with open('test_event.json', 'w') as f:
    json.dump(data, f)

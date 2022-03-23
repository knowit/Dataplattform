from dataplattform.testing.events import APIGateway

from json import dumps, load

import os

with (open(os.path.join(os.path.dirname(__file__), 'test_data.json'), 'r')) as json_file:
    body = dumps(load(json_file))

event = APIGateway(headers={}, body=body)

with open('test_event.json', 'w') as outfile:
    outfile.write(event.to_json())
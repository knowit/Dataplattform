import json
from common_lib.common.services.cache_table_service import delete_cache_table


def handler(event, context):
    records = event['Records']

    def load_message(record):
        rec = record.get('Sns')
        return rec.get('Subject', None), rec.get('Message', None)

    messages = [(topic, json.loads(msg)) for topic, msg in [
        load_message(record) for record in records
    ] if topic]

    for topic, message in messages:
        if topic == 'DeleteReport':
            delete_cache_table(
                message['dataProtection'],
                message['name'])

    return {}

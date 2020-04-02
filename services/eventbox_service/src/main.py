import json
import logging
from util.database import create_tables, Session
from util.schemas import eventSchema

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_events(e, context):
    # TODO: Should filter by creator
    session = Session()
    result = session.query(Event).all()
    session.close()
    logger.info('Get events')
    return {
        'statusCode': 200,
        'body': [eventSchema.dumps(e) for e in result],
        'body': 'test'
    }

def get_event(e, context):
    event_id = e['pathParameters']['id']

    session = Session()
    result = session.query(Event).filter(Event.id == event_id).first()
    session.close()
    
    return {
        'statusCode': 200,
        'body': eventSchema.dumps(result)
    }

def add_event(e, context):
    event = eventSchema.loads(e['body'])
    
    session = Session()
    session.add(event)
    session.commit()
    session.close()

    return {
        'statusCode': 200,
        'body': 'Success'
    }

def delete_event(e, context):
    # TODO
    return {
        'statusCode': 200,
        'body': 'Hello from delete event'
    }

def update_event(e, context):
    # TODO
    return {
        'statusCode': 200,
        'body': 'Hello from update event'
    }

def createDb(event, context):
    create_tables()

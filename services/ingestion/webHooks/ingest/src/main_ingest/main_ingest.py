import json

def handler(event, context):
    data_type = event["pathParameters"]["type"]
    data = event["body"]

    return {
        'statusCode': 200,
        'body': json.dumps({
            "message": "success!",
            "data_type": data_type,
            "data": data
        })
    }


import boto3
import os


def configure(event, context):
    client = boto3.client("ssm")
    param_name = os.environ['SSM_PARAM_NAME_CLIENT_ID']
    client_id = os.environ['CLIENT_ID']
    try:
        result = client.put_parameter(
            Name=param_name,
            Value=client_id,
            Type="String"
        )
        return dict(
            statusCode=200,
            body=result
        )
    except Exception as e:
        return dict(
            statusCode=500,
            body=str(e)
        )

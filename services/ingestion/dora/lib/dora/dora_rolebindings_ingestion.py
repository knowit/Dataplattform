import boto3
from datetime import datetime

quicksight_client = boto3.client("quicksight")
sts_client = boto3.client("sts")
account_id = sts_client.get_caller_identity().get('Account')


def handler(event, context):
    dt_string = datetime.now().strftime("%Y%m%d-%H%M%S")
    ingestion_id = f"{dt_string}-Rolebinding"

    try:
        quicksight_client.create_ingestion(AwsAccountId=account_id, DataSetId="Rolebinding",
                                           IngestionId=ingestion_id)
    except:
        return False
    return {
        'message': 'success!'
    }

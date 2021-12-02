import boto3
import os
import json
from datetime import datetime

quicksight_client = boto3.client("quicksight")
sts_client = boto3.client("sts")
account_id = sts_client.get_caller_identity().get('Account')

data_sets = ["DeploymentFrequency-id", "DeploymentsNullValues-id"]

def handler(event, context):
    def create_ingestion(account_id, data_set_ids):
        
        for data_set_id in data_set_ids:
            dt_string = datetime.now().strftime("%Y%m%d-%H%M%S")
            ingestion_id = f"{dt_string}-{data_set_id}"

            try:
                response = quicksight_client.create_ingestion(AwsAccountId = account_id, DataSetId=data_set_id, IngestionId = ingestion_id)
            except:
                return False
        return response

    response = create_ingestion(account_id, data_sets)

    return {
        'message': response
    }
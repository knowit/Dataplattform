from ast import Try
import boto3
from botocore.exceptions import ClientError
import json
import time


glue_client = boto3.client('glue', region_name = 'eu-central-1')
cf_client = boto3.client('cloudformation')
athena_client = boto3.client('athena')
lambda_client = boto3.client('lambda')

workgroup = "DoraWorkgroups"


def handler(event, context):

    def s3_ingestion():
        #Performs an ingestion
        response = lambda_client.invoke(
            FunctionName='dev-dora-ingest', 
            InvocationType='RequestResponse'
        )
        return response

    def run_crawler():
        response = ""
        try:
            response = glue_client.start_crawler(Name='DoraCrawlers')
        except:
            pass
        wait_until_ready(5) #Check every 5 seconds
        return response

    def wait_until_ready(retry_seconds) -> None:
        # Checks if the crawler has finished running. 
        state_previous = None
        while True:
            response_get = glue_client.get_crawler(Name='DoraCrawlers')
            state = response_get["Crawler"]["State"]
            if state != state_previous:
                state_previous = state
            if state == "READY":  # Other known states: RUNNING, STOPPING
                return
            time.sleep(retry_seconds)


    def get_saved_queries(query_ids):
        response = athena_client.batch_get_named_query(
            NamedQueryIds=query_ids
        )
        return response['NamedQueries']

    def map_name_to_query(dictionary):
        queries = {}
        for item in dictionary:
            queries[item["Name"]] = item["QueryString"].replace('\n', ' ') #Without ' ' it puts two words together, with ' ' it adds huge spaces. FInd better method
        return queries

    def get_query_id():
        response = athena_client.list_named_queries(
            MaxResults=10,
            WorkGroup=workgroup
        )
        return response['NamedQueryIds']


    def query_execution(query_string):
        response = athena_client.start_query_execution(
            QueryString=query_string,
            QueryExecutionContext={
                'Database': 'dev_level_4_database',
                'Catalog': 'AWSDataCatalog'
            },
            WorkGroup=workgroup
        )

    def run_athena_query(queries):
        # To run them in the correct order
        query_execution(queries['Frequency'])
        query_execution(queries['GithubDeployments'])	
        query_execution(queries['GithubDeploymentsWithNullValues'])
        query_execution(queries['DeploymentFrequency'])

    s3_ingestion()
    run_crawler()
    query_information = get_saved_queries(get_query_id())
    queries = map_name_to_query(query_information)
    run_athena_query(queries)

    return {
        'message': 'success!'
    }
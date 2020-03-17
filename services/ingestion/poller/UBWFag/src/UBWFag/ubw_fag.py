import boto3
import json
import time
from os import environ
from zeep import Client
from xmltodict import parse


def handler(event, context):
    poll()
    return {'statusCode': 200, 'body': 'Success'}


def ssm_parameters():
    path = f'{environ.get("STAGE")}/{environ.get("SERVICE")}'
    client = boto3.client('ssm')
    return (
        client.get_parameter(
            Name=f'/{path}/UBW_USERNAME', WithDecryption=True)['Parameter']['Value'],
        client.get_parameter(
            Name=f'/{path}/UBW_PASSWORD', WithDecryption=True)['Parameter']['Value'],
        client.get_parameter(
            Name=f'/{path}/UBW_CLIENT', WithDecryption=True)['Parameter']['Value'],
        client.get_parameter(
            Name=f'/{path}/UBW_URL', WithDecryption=False)['Parameter']['Value'],
        client.get_parameter(
            Name=f'/{path}/UBW_TEMPLATE_ID', WithDecryption=True)['Parameter']['Value'])


def poll():
    username, password, client, url, template_id = ssm_parameters()

    soap_client = Client(wsdl=f'{url}?QueryEngineService/QueryEngineV200606DotNet')
    res = soap_client.service.GetTemplateResultAsXML(
        input={
            'TemplateId': template_id,
            'TemplateResultOptions': {
                'ShowDescriptions': True,
                'Aggregated': True,
                'OverrideAggregation': False,
                'CalculateFormulas': True,
                'FormatAlternativeBreakColumns': True,
                'RemoveHiddenColumns': False,
                'FirstRecord': -1,
                'LastRecord': -1
            },
            'SearchCriteriaPropertiesList': {
                'SearchCriteriaProperties': [
                    {
                        'ColumnName': 'timecode',
                        'Description': 'Tidskode',
                        'RestrictionType': '!()',
                        'FromValue': "'X9'",
                        'DataType': 10,
                        'DataLength': 25,
                        'DataCase': 2,
                        'IsParameter': True,
                        'IsVisible': False,
                        'IsPrompt': False
                    }
                ]
            },
        },
        credentials={
            'Username': username,
            'Client': client,
            'Password': password,
        })

    ubw_data = parse(res['TemplateResult'])['Agresso']['AgressoQE']

    path = environ.get("ACCESS_PATH")
    s3 = boto3.resource('s3')
    s3_object = s3.Object(environ.get('DATALAKE'), f"{path}/" + str(int(time.time())) + ".json")
    s3_object.put(Body=(bytes(json.dumps(ubw_data).encode('UTF-8'))))


if __name__ == "__main__":
    poll()

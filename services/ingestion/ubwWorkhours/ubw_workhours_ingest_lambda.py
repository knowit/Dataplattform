from dataplattform.common.handlers.ingest import IngestHandler
from dataplattform.common.aws import SSM
from dataplattform.common.schema import Data, Metadata
from datetime import datetime
from xmltodict import parse
from zeep import Client


handler = IngestHandler()


@handler.ingest()
def ingest(event) -> Data:
    username, password, client, template_id = SSM(
        with_decryption=True
    ).get('UBW_USERNAME', 'UBW_PASSWORD', 'UBW_CLIENT', 'UBW_TEMPLATE_ID')

    url = SSM().get('UBW_URL')

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
            }
        },
        credentials={
            'Username': username,
            'Client': client,
            'Password': password,
        })

    return Data(
        metadata=Metadata(timestamp=datetime.now().timestamp()),
        data=parse(res['TemplateResult'])['Agresso']['AgressoQE']
    )

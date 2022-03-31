from dataplattform.common.handlers.ingest import IngestHandler
from dataplattform.common.aws import SSM
from dataplattform.common.schema import Data, Metadata
from dataplattform.query.engine import Athena
from datetime import datetime
from xmltodict import parse
from zeep import Client


handler = IngestHandler()
ath = Athena()


@handler.ingest()
def ingest(event) -> Data:
    def ubw_record_filter(record):
        if "tab" not in record or "reg_period" not in record:
            return False

        # Only the "B" documents are completed, the rest should be ignored.
        if record["tab"] != "B":
            return False

        # You should only uploads docs that are older than 4 weeks.
        year, week = record["reg_period"][0:4], record["reg_period"][4:]
        cur_year, cur_week = datetime.now().isocalendar()[0:2]

        number_of_weeks = int(year) * 52 + int(week)
        current_number_of_weeks = cur_year * 52 + cur_week
        if number_of_weeks > current_number_of_weeks - 4:
            return False

        return True

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
    return Data(
        metadata=Metadata(timestamp=datetime.now().timestamp()),
        data=[rec for rec in ubw_data if ubw_record_filter(rec)]
    )

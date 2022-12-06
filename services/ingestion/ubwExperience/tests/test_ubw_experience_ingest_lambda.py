from ubwexperience.ubw_experience_ingest_lambda import handler
from pytest import fixture
from json import loads


@fixture(autouse=True)
def zeep_ubw_mock(mocker):
    mock = mocker.Mock()
    mock.service.GetTemplateResultAsXML.return_value = {
        "ReturnCode": 0,
        "Status": None,
        "TemplateResult": """
            <Agresso>
                <AgressoQE>
                   <resource_id>1</resource_id>
                   <tab>A</tab>
                   <name>Test A</name>
                   <r0_x0023_exami0_x0023_612>1</r0_x0023_exami0_x0023_612>
                   <xr0_x0023_e1_x0023_611_x0023_U00> Master of science </xr0_x0023_e1_x0023_611_x0023_U00>
                    <date_from>2020-03-16T00:00:00+01:00</date_from>
                </AgressoQE>
                <AgressoQE>
                    <resource_id>2</resource_id>
                    <name>Test B</name>
                    <r0_x0023_exami0_x0023_612>2</r0_x0023_exami0_x0023_612>
                    <xr0_x0023_e1_x0023_611_x0023_U00> Master of science </xr0_x0023_e1_x0023_611_x0023_U00>
                    <date_from>2020-03-16T00:00:00+01:00</date_from>
                </AgressoQE>
                <AgressoQE>
                    <resource_id>3</resource_id>
                    <name>Test C</name>
                    <r0_x0023_exami0_x0023_612>3</r0_x0023_exami0_x0023_612>
                    <xr0_x0023_e1_x0023_611_x0023_U00> Master of science </xr0_x0023_e1_x0023_611_x0023_U00>
                    <date_from>2020-03-16T00:00:00+01:00</date_from>
                </AgressoQE>
            </Agresso>
        """
    }
    mocker.patch('ubwexperience.ubw_experience_ingest_lambda.Client', return_value=mock)

    yield mock


def test_handler_metadata(s3_bucket):
    handler(None, None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())

    assert 'timestamp' in data['metadata']


def test_handler_data_length(s3_bucket):
    handler(None, None)

    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())

    assert len(data['data']) == 3


def test_handler_data(s3_bucket):
    handler(None, None)
    response = s3_bucket.Object(next(iter(s3_bucket.objects.all())).key).get()
    data = loads(response['Body'].read())

    assert data['data'][0]['tab'] == 'A' and\
        data['data'][0]['name'] == 'Test A' and\
        data['data'][0]['resource_id'] == '1'

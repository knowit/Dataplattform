from ubw_customer_per_resource_ingest_lambda import handler
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
                    <_recno>0</_recno>
                    <_section>D</_section>
                    <tab>B</tab>
                    <reg_period>202053</reg_period>
                    <used_hrs>4</used_hrs>
                    <f0_billable>0</f0_billable>
                    <resource_id>X1</resource_id>
                    <xresource_id>X1_name</xresource_id>
                    <r1project>XX</r1project>
                    <xr1project>Local Projects</xr1project>
                    <xr0work_order />
                    <work_order>work order no 1</work_order>
                    <xwork_order>Some work order desc.</xwork_order>
                </AgressoQE>
                <AgressoQE>
                    <_recno>0</_recno>
                    <_section>D</_section>
                    <tab>B</tab>
                    <reg_period>202053</reg_period>
                    <used_hrs>1</used_hrs>
                    <f0_billable>1</f0_billable>
                    <resource_id>X1</resource_id>
                    <xresource_id>X1_name</xresource_id>
                    <r1project>XX</r1project>
                    <xr1project>External Projects</xr1project>
                    <xr0work_order />
                    <work_order>work order no 2</work_order>
                    <xwork_order>Some work order desc.</xwork_order>
                </AgressoQE>
                <AgressoQE>
                    <_recno>0</_recno>
                    <_section>D</_section>
                    <tab>A</tab>
                    <reg_period>202053</reg_period>
                    <used_hrs>1</used_hrs>
                    <resource_id>X2</resource_id>
                    <f0_billable>1</f0_billable>
                    <xresource_id>X2_name</xresource_id>
                    <r1project>XX</r1project>
                    <xr1project>External Projects</xr1project>
                    <xr0work_order />
                    <work_order>work order no 2</work_order>
                    <xwork_order>Some work order desc.</xwork_order>
                </AgressoQE>
            </Agresso>
        """
    }
    mocker.patch('ubw_customer_per_resource_ingest_lambda.Client', return_value=mock)

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

    assert data['data'][0]['tab'] == 'B' and\
        data['data'][0]['reg_period'] == '202053' and\
        data['data'][0]['used_hrs'] == '4'

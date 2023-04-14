from moto import mock_ssm
import boto3
import dataplattform.cli.commands.add_ssm as add_ssm


@mock_ssm
def test_add_parameter():
    client = boto3.client('ssm')
    parameter_name = add_ssm.add_parameter(
        stage="TestStage",
        service="TestService",
        name="TestName",
        value="TestValue",
        type_="String",
        description="TestDescription",
        overwrite=True,
        tags=[
            {
                "Key": "TestTag1",
                "Value": "TestTag1Value"
            },
            {
                "Key": "TestTag2",
                "Value": "TestTag2Value"
            }
        ]
    )
    assert parameter_name == "/TestStage/TestService/TestName"
    assert client.get_parameter(Name=parameter_name)["Parameter"] is not None
    assert client.get_parameter(Name=parameter_name)["Parameter"]["Type"] == "String"
    assert client.get_parameter(Name=parameter_name)["Parameter"]["Value"] == "TestValue"

    tags = client.list_tags_for_resource(
        ResourceType="Parameter",
        ResourceId=parameter_name
    )["TagList"]
    assert tags[0]["Key"] == "TestTag1"
    assert tags[0]["Value"] == "TestTag1Value"
    assert tags[1]["Key"] == "TestTag2"
    assert tags[1]["Value"] == "TestTag2Value"

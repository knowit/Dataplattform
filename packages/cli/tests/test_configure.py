from moto import mock_ssm
import dataplattform.cli.commands.configure as configure
import pytest


@mock_ssm
def test_get_client():
    assert len(configure.regional_clients) == 1
    client_1 = configure.get_client(None)
    assert client_1.meta.region_name == "eu-central-1"
    assert len(configure.regional_clients) == 1
    client_2 = configure.get_client("us-east-1")
    assert client_2.meta.region_name == "us-east-1"
    assert len(configure.regional_clients) == 2


@mock_ssm
def test_get_regions():
    regions_1 = configure.get_regions({
        "Regions": ["us-east-1", "eu-central-2"]
    })
    assert regions_1 == ["us-east-1", "eu-central-2"]
    regions_2 = configure.get_regions({})
    assert regions_2 == ["eu-central-1"]


@mock_ssm
def test_dict_is_parameter():
    assert configure.dict_is_parameter({"Value": "Test"}) is True
    assert configure.dict_is_parameter({"Foo": "bar"}) is False
    assert configure.dict_is_parameter({}) is False


@mock_ssm
def test_get_parameter_type():
    assert configure.get_parameter_type({}) == "SecureString"
    assert configure.get_parameter_type({"Type": "String"}) == "String"
    assert configure.get_parameter_type({"Type": "StringList"}) == "StringList"
    with pytest.raises(ValueError):
        configure.get_parameter_type({"Type": "InvalidType"})


@mock_ssm
def test_add_parameter_recursively():
    client_1 = configure.get_client(None)
    client_2 = configure.get_client("us-east-1")

    configure.add_parameter_recursively({})
    assert len(client_1.get_parameters_by_path(Path="/", Recursive=True)["Parameters"]) == 0
    assert len(client_2.get_parameters_by_path(Path="/", Recursive=True)["Parameters"]) == 0
    with pytest.raises(ValueError):
        configure.add_parameter_recursively({
            "SomeKey": {
                "Value": "Test123",
                "Type": "SomeInvalidType"
            }
        })

    configure.add_parameter_recursively({
        "SomeKey": {
            "Value": "Test123"
        }
    })
    assert len(client_1.get_parameters_by_path(Path="/", Recursive=True)["Parameters"]) == 1
    assert len(client_2.get_parameters_by_path(Path="/", Recursive=True)["Parameters"]) == 0
    assert client_1.get_parameter(Name="/SomeKey")["Parameter"]["Value"] == "kms:alias/aws/ssm:Test123"
    assert client_1.get_parameter(Name="/SomeKey")["Parameter"]["Type"] == "SecureString"

    configure.add_parameter_recursively({
            "SomeKey": {
                "SomeRecursiveKey": {
                    "TestKey1": {
                        "Value": "Test_1",
                        "Type": "String",
                        "Regions": [
                            "eu-central-1",
                            "us-east-1"
                        ]
                    }
                },
                "SomeOtherKey": [
                    "TestValue1",
                    "TestValue2"
                ]
            }
        },
        path="/test/path/1")
    assert len(client_1.get_parameters_by_path(Path="/", Recursive=True)["Parameters"]) == 2
    assert len(client_1.get_parameters_by_path(Path="/test", Recursive=True)["Parameters"]) == 1
    assert len(client_2.get_parameters_by_path(Path="/", Recursive=True)["Parameters"]) == 1
    assert len(client_2.get_parameters_by_path(Path="/test", Recursive=True)["Parameters"]) == 1
    assert client_1.get_parameter(
        Name="/test/path/1/SomeKey/SomeRecursiveKey/TestKey1"
    )["Parameter"]["Value"] == "Test_1"
    assert client_1.get_parameter(
        Name="/test/path/1/SomeKey/SomeRecursiveKey/TestKey1"
    )["Parameter"]["Type"] == "String"
    assert client_2.get_parameter(
        Name="/test/path/1/SomeKey/SomeRecursiveKey/TestKey1"
    )["Parameter"]["Value"] == "Test_1"
    assert client_2.get_parameter(
        Name="/test/path/1/SomeKey/SomeRecursiveKey/TestKey1"
    )["Parameter"]["Type"] == "String"

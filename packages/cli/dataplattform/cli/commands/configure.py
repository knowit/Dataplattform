from argparse import ArgumentParser, Namespace
import boto3
import yaml

client = boto3.client('ssm')


def dict_is_parameter(config: dict) -> bool:
    return "Value" in config


def get_parameter_type(config: dict) -> str:
    if "Type" in config:
        return config["Type"]
    else:
        return "String"


def add_parameter_recursively(config: dict, path: str = ""):
    for key in config:
        value = config.get(key)
        if type(value) is dict:
            full_name = path + "/" + key
            if dict_is_parameter(value):
                param_type = get_parameter_type(value)
                try:
                    client.put_parameter(
                        Name=full_name,
                        Value=value["Value"],
                        Type=param_type,
                        Overwrite=True,
                        Tier='Standard'
                    )
                    print(
                        "Parameter set successfully: " + full_name)
                except Exception as e:
                    print("Failed to set SSM-parameter: " + full_name + ".\nStack trace:\n" + str(e))

            else:
                add_parameter_recursively(value, path=full_name)


def init(parser: ArgumentParser):
    parser.add_argument('-c', '--config-file', dest="config_file", default=False)
    parser.add_argument('-s', '--stage', default="dev")


def run(args: Namespace, _):
    path = args.config_file
    try:
        config = yaml.load(open(path), Loader=yaml.FullLoader)
        config_path = "/" + args.stage
        add_parameter_recursively(config[args.stage], path=config_path)

    except KeyError:
        print("Error: No configuration was found for in " + path + " for stage: " + args.stage)

    except Exception as e:
        print("Failed to parse config yaml file: " + path + ".\nStack trace:\n" + str(e))

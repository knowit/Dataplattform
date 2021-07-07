from argparse import ArgumentParser, Namespace
import boto3
import yaml

default_client = boto3.client('ssm')
default_region = default_client.meta.region_name
regional_clients = dict({str(default_region): default_client})


def get_client(region: str):
    r = default_region if region is None else region
    if r not in regional_clients.keys():
        regional_clients[r] = boto3.client('ssm', region_name=r)
    return regional_clients[r]


def get_regions(config: dict) -> list:
    return config.get("Regions", [default_region])


def dict_is_parameter(config: dict) -> bool:
    return "Value" in config


def get_parameter_type(config: dict) -> str:
    types = ["String", "StringList", "SecureString"]
    param_type = config.get("Type", "SecureString")
    if param_type not in types:
        raise ValueError('Invalid parameter type: ' + param_type + ". Must be one of the following: " + str(types))
    else:
        return param_type


def add_parameter_recursively(config: dict, path: str = ""):
    for key in config:
        value = config.get(key)
        if type(value) is dict:
            full_name = path + "/" + key
            if dict_is_parameter(value):
                param_type = get_parameter_type(value)
                for region in get_regions(value):
                    client = get_client(region)
                    try:
                        client.put_parameter(
                            Name=full_name,
                            Value=str(value["Value"]),
                            Type=param_type,
                            Overwrite=True,
                            Tier='Standard'
                        )
                        print(
                            "(" + region + ") - Parameter set successfully: " + full_name)
                    except Exception as e:
                        print("Failed to set SSM-parameter: " + full_name + ".\nStack trace:\n" + str(e))
                        pass

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
        pass

    except Exception as e:
        print("Failed to parse config yaml file: " + path + ".\nStack trace:\n" + str(e))
        pass

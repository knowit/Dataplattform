from argparse import ArgumentParser, Namespace
import boto3
import yaml

client = boto3.client('ssm')


def add_parameter_recursively(config: dict, path: str = ""):
    for key in config:
        value = config.get(key)
        if type(value) is dict:
            add_parameter_recursively(value, path + "/" + key)
        else:
            name = path + "/" + key
            try:
                client.put_parameter(
                    Name=name,
                    Value=value,
                    Type="String",
                    Overwrite=True,
                    Tier='Standard'
                )
                print("Parameter set successfully: " + name)
            except Exception as e:
                print("Failed to set SSM-parameter. Stack trace:\n" + str(e))


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
        print("Failed to parse config yaml file: " + path + ". Stack trace:\n" + str(e))

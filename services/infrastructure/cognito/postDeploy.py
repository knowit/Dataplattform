import boto3
import argparse
import traceback


def get_cf_outputs(stack_name: str) -> dict:
    client = boto3.client('cloudformation')
    response = client.describe_stacks(StackName=stack_name)
    result = dict()
    for output in response["Stacks"][0]["Outputs"]:
        key = output["OutputKey"]
        value = output["OutputValue"]
        result[key] = value
    return result


def set_ssm_parameter(name: str, value: str, param_type: str = "String"):
    client = boto3.client('ssm')
    try:
        client.put_parameter(
            Name=name,
            Value=value,
            Type=param_type,
            Overwrite=True,
            Tier='Standard'
        )
        print("Successfully set SSM parameter: " + name)
    except Exception as e:
        print("\nFailed to set SSM parameter: " + name)
        traceback.print_stack()
        raise e


if __name__ == '__main__':
    ap = argparse.ArgumentParser()

    ap.add_argument("--stack-name",
                    required=True,
                    dest="stack_name")

    ap.add_argument("--param-name",
                    required=True,
                    dest="param_name")

    kwargs = vars(ap.parse_args())

    outputs = get_cf_outputs(kwargs['stack_name'])

    client_id = outputs["CognitoUserPoolClientId"]
    param_name = kwargs["param_name"]

    print("\nConfiguring SSM...")
    set_ssm_parameter(param_name, client_id)
    print("Configuration complete!\n")

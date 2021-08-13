import boto3
import argparse
import subprocess
import traceback


client = boto3.client('cloudformation', region_name='eu-central-1')


def get_cf_outputs(stack_name: str) -> dict:
    response = client.describe_stacks(StackName=stack_name)
    result = dict()
    for output in response["Stacks"][0]["Outputs"]:
        key = output["OutputKey"]
        value = output["OutputValue"]
        result[key] = value
    return result


def run_command(cmd: str) -> None:
    print("Running: " + cmd)

    if subprocess.call(cmd, shell=True) != 0:
        raise Exception("Exception occurred during post-deployment script:\n"
                        + str('\n'.join(traceback.format_list(traceback.extract_stack()))))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()

    ap.add_argument("--stack-name",
                    required=True,
                    help="The full name of the CloudFormation stack.",
                    dest="stack_name")

    kwargs = vars(ap.parse_args())

    outputs = get_cf_outputs(kwargs["stack_name"])

    try:
        run_command("yarn build")
        run_command("aws s3 sync dist s3://" + outputs["StaticBucketOutput"])
        run_command("aws cloudfront create-invalidation --paths /  --distribution-id " + outputs["DistributionId"])
    except Exception as e:
        raise e





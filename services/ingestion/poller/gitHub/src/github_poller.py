import boto3
import os
import json
import time
import requests


url = 'https://api.github.com/orgs/knowit/repos'


def handler(event, context):
    poll()

    return {
        'statusCode': 200,
        'body': 'Success'
    }


def poll():
    res = requests.get(url)
    repos = res.json()
    while 'next' in res.links.keys():
        res = requests.get(res.links['next']['url'])
        repos.extend(res.json())

    data = {
        'metadata': {
            'timestamp': time.time(),
            'event': 'repo'
        },
        'data': repos
    }

    path = os.getenv("ACCESS_PATH")

    s3 = boto3.resource('s3')
    s3_object = s3.Object(os.getenv('DATALAKE'), path + str(int(time.time())) + ".json")
    s3_object.put(Body=(bytes(json.dumps(data).encode('UTF-8'))))

    return True


if __name__ == "__main__":
    poll()

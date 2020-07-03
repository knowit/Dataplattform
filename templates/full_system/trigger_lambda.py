from multiprocessing import Pool
from boto3 import client


def test_invoke_lambda(n):
    lambda_client = client('lambda')
    res = lambda_client.invoke(
        FunctionName='dev-test-lambda-ingest',
        InvocationType='RequestResponse')
    return f'lambda invoke {n} done: {res["StatusCode"]}'


N = 10
if __name__ == '__main__':
    with Pool(N) as p:
        print(p.map(test_invoke_lambda, range(N)))

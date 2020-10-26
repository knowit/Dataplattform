from dataplattform.common.helper import Helper


def handler(event, context):
    return {
        'statusCode': Helper().download_from_http(event.get('body', {}))
    }

from dataplattform.common.helper import download_from_http


def handler(event, context):
    return {
        'statusCode': download_from_http(event.get('body'))
    }

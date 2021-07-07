from dataplattform.common.raw_storage import write_file_to_bucket
from urllib import request
from os import environ


def handler(event, context):
    http_request = event['body']

    url = http_request.get('requestUrl')
    if not url:
        return 400
    headers = http_request.get('header', {})
    filetype = event.get('filetype')

    valid_content_types = {'pdf':  'application/pdf',
                           'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                           'jpg':  'image/jpeg'}

    if filetype not in list(valid_content_types.keys()):
        return 400

    req = request.Request(url)
    for (header, value) in headers.items():
        req.add_header(header, value)

    bucket = environ.get('PUBLIC_BUCKET')

    response = request.urlopen(req)
    content_type = response.getheader('Content-Type')
    if content_type == valid_content_types[filetype]:
        if response.status == 200 and response.readable():
            write_file_to_bucket(data=response.read(),
                                 filename=event['filename'],
                                 bucket=bucket)
        else:
            return 400
    else:
        return 400
    return response.status

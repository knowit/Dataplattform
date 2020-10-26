from dataplattform.common.raw_storage import RawStorage
import boto3
from urllib import request


class Helper():
    def launch_async_lambda(self, payload: bytes, lambda_name: str = None):
        download_lambda = boto3.client('lambda')
        download_lambda.invoke(FunctionName=lambda_name,
                               InvocationType='Event',
                               Payload=payload)

    def download_from_http(self, body: dict = {}):
        url = body.get('requestUrl')
        headers = body.get('header', {})
        filetype = body.get('filetype')

        valid_content_types = {'pdf':  'application/pdf',
                               'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                               'jpg':  'image/jpeg'}

        if filetype not in list(valid_content_types.keys()):
            return 400

        req = request.Request(url)
        for (header, value) in headers.items():
            req.add_header(header, value)

        response = request.urlopen(req)
        content_type = response.getheader('Content-Type')
        if content_type == valid_content_types[filetype]:
            if (response.status == 200 and response.readable()):
                RawStorage().write_file_to_bucket(data=response.read(),
                                                  filename=body['filename'],
                                                  bucket=body['bucket'])
            else:
                return 400
        else:
            return 400
        return response.status

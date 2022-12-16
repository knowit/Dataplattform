from botocore.exceptions import ClientError
from flask import jsonify
import logging

from common_lib.common.repositories.catalogue import GlueRepositoryNotFoundException


# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/error-handling.html#parsing-error-responses-and-catching-exceptions-from-aws-services
def handle_client_error(error: ClientError):
    error_code = error.response.get('ResponseMetadata', {}).get('HTTPStatusCode', 500)
    error_message = error.response.get('Error', {'Message': 'Unknown error'})
    error_message['RequestId'] = error.response.get('ResponseMetadata', {}).get('RequestId')
    logging.error(str(error_message), exc_info=error)

    if error_message['Code'] == 'AccessDeniedException':  # Obfuscate internal information
        error_message['Message'] = 'User does not have access to resource'

    return jsonify(error_message), error_code


def handle_value_error(e: ValueError):
    return jsonify({'Message': str(e)}), 400


def handle_not_found(e: GlueRepositoryNotFoundException):
    return jsonify({'Message': str(e)}), 404


def handle_any(e: Exception):
    logging.error(str(e), exc_info=e)
    return jsonify({'message': 'Internal Server Error'}), 500

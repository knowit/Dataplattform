import logging

from botocore.exceptions import ClientError
from common_lib.common.repositories.catalogue import GlueRepositoryNotFoundException
from werkzeug.exceptions import HTTPException


# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/error-handling.html#parsing-error-responses-and-catching-exceptions-from-aws-services
def handle_client_error(error: ClientError):
    status_code = error.response.get('ResponseMetadata', {}).get('HTTPStatusCode', 500)
    error_message = error.response.get('Error', {'Message': 'Unknown error'})
    logging.getLogger().warning("client error" + str(error_message), exc_info=error)

    if error_message['Code'] == 'AccessDeniedException':  # Obfuscate internal information
        error_message['Message'] = 'User does not have access to resource'
        status_code = 403  # Seems like ClientError does not provide the correct mapping here...

    error_response = {
        'errorType': error_message['Code'],
        'message': error_message['Message'],
        'requestId': error.response.get('ResponseMetadata', {}).get('RequestId')
    }

    return error_response, status_code


def handle_value_error(e: ValueError):
    logging.getLogger().warning("value error: " + str(e))
    return {'message': str(e)}, 400


def handle_not_found(e: GlueRepositoryNotFoundException):
    logging.getLogger().warning("repo not found error: " + str(e))
    return {'message': str(e)}, 404


def handle_any(e: Exception):
    logging.getLogger().error("unhandled exception: " + str(e), exc_info=e)

    if isinstance(e, HTTPException):
        return {
            'code': e.code,
            'name': e.name,
            'message': e.description,
        }, e.code
    else:
        return {'message': 'Internal Server Error'}, 500

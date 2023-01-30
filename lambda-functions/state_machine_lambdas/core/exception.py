import logging
import traceback

from botocore.exceptions import ClientError

log = logging.getLogger()
log.setLevel(logging.ERROR)


# Boto exception keys
RESPONSE_METADATA_KEY = "ResponseMetadata"
REQUEST_ID_KEY = "RequestId"

def log_exception(exception: Exception):
    """Performs standard logging for exceptions across all lambdas"""
    if isinstance(exception, ClientError):
        log.error(f'Failed to execute API: {exception.operation_name} & {exception.response}')
    log.error(f'Failed with error: {exception} & stack trace: {traceback.format_exc()}')

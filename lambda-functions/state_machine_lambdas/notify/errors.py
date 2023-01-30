# Constants
FAILURE_REASON_LENGTH_LIMIT: int = 2048
LAMBDA_TIMEOUT_ERROR: str = 'States.Timeout'
LAMBDA_TIMEOUT_FAILURE_REASON: str = 'A lambda function invoked by the state machine has timed out'

# Input event keys
ERROR_KEY: str = 'error'
ERROR_MESSAGE_KEY: str = 'errorMessage'

def workflow_has_error(event: dict) -> bool:
    """Determines if an error has occurred in the workflow based on a lambda input event"""
    return ERROR_MESSAGE_KEY in event and ERROR_KEY in event

def get_failure_reason(event: dict) -> str:
    """Gets the SC failure reason based on error and error message in a lambda input event"""
    error_message = event[ERROR_MESSAGE_KEY]
    if event[ERROR_KEY] == LAMBDA_TIMEOUT_ERROR:
        return LAMBDA_TIMEOUT_FAILURE_REASON
    elif len(error_message) <= FAILURE_REASON_LENGTH_LIMIT:
        return error_message
    else:
        return error_message[:FAILURE_REASON_LENGTH_LIMIT - 3] + '...'

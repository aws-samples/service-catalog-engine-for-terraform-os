import json
import logging
import os

import boto3

from core.configuration import Configuration
from core.exception import log_exception

log = logging.getLogger()
log.setLevel(logging.INFO)

# Globals
app_config = None
s3_resource_client = None
state_bucket_name = None

# Input and output keys
PROVISIONED_PRODUCT_ID_KEY = 'provisionedProductId'
AWS_ACCOUNT_ID_KEY = "awsAccountId"
RECORD_OUTPUTS_KEY = 'recordOutputs'
RECORD_OUTPUT_KEY_KEY = 'key'
RECORD_OUTPUT_VALUE_KEY = 'value'
RECORD_OUTPUT_DESCRIPTION_KEY = 'description'

# State file keys
STATE_FILE_OUTPUTS_KEY = 'outputs'
STATE_FILE_OUTPUTS_VALUE_KEY = 'value'
STATE_FILE_OUTPUTS_DESCRIPTION_KEY = 'description'
STATE_FILE_OUTPUTS_SENSITIVE_KEY = 'sensitive'

#Constants
SENSITIVE_VALUE_MARKER = '(sensitive value)'

# Environment variable keys
STATE_BUCKET_NAME_KEY = 'STATE_BUCKET_NAME'

def __validate_event(event: dict):
    """Validates that all required fields are in the Lambda event and have expected values

    Parameters
    ----------
    event: dict, required
        The Lambda event to be validated
    """

    if PROVISIONED_PRODUCT_ID_KEY not in event:
        raise RuntimeError(f'{PROVISIONED_PRODUCT_ID_KEY} must be provided')
    if AWS_ACCOUNT_ID_KEY not in event:
        raise RuntimeError(f'{AWS_ACCOUNT_ID_KEY} must be provided')

def __fetch_state_file_from_s3(bucket_name: str, key: str) -> dict:
    """Fetch state file dict from the provided S3 state bucket

    Parameters
    ----------
    bucket_name: str, required
        The name of the state file bucket in S3

    key: str, required
        The name of the state file key in S3

    Returns
    -------
        dict: The content returned by S3
    """

    content_object = s3_resource_client.Object(bucket_name, key)
    state_file_content = content_object.get()['Body'].read().decode()

    try:
        return json.loads(state_file_content)
    except ValueError:
        raise RuntimeError(f'File {key} in bucket {bucket_name} is not in JSON format')

def __sanitize_output_value(output_block: dict) -> str:
    """Returns a sanitized value for a record output

    Parameters
    ----------
    output_block: dict, required
        The dict containing the block for one output in the state file contents

    Returns
    -------
        str: The sanitized version of the output block's value
    """
    if STATE_FILE_OUTPUTS_SENSITIVE_KEY in output_block and output_block[STATE_FILE_OUTPUTS_SENSITIVE_KEY]:
        return SENSITIVE_VALUE_MARKER
    else:
        return str(output_block[STATE_FILE_OUTPUTS_VALUE_KEY])

def __parse_outputs_from_state_file(state_file_content: dict) -> list:
    """Parse outputs from state file to fetch record outputs

    Parameters
    ----------
    state_file_content: dict, required
        The dict of state file

    Returns
    -------
        list: The list of record outputs
    """
    record_outputs = []

    if STATE_FILE_OUTPUTS_KEY not in state_file_content:
        return record_outputs

    outputs_block = state_file_content[STATE_FILE_OUTPUTS_KEY]

    for output_key in outputs_block:
        record_output = {RECORD_OUTPUT_KEY_KEY: output_key}

        if STATE_FILE_OUTPUTS_VALUE_KEY not in outputs_block[output_key]:
            raise RuntimeError(f'Output value is missing for output {output_key}')

        record_output[RECORD_OUTPUT_VALUE_KEY] = __sanitize_output_value(outputs_block[output_key])

        if STATE_FILE_OUTPUTS_DESCRIPTION_KEY not in outputs_block[output_key]:
            record_output[RECORD_OUTPUT_DESCRIPTION_KEY] = None
        else:
            record_output[RECORD_OUTPUT_DESCRIPTION_KEY] = outputs_block[output_key][STATE_FILE_OUTPUTS_DESCRIPTION_KEY]

        record_outputs.append(record_output)

    return record_outputs

def parse(event, context) -> dict:
    """Lambda handler to parse state file JSON from S3 state bucket to fetch record outputs

    Parameters
    ----------
    event: dict, required
        The input event to the Lambda function

    context: object, required
        Lambda Context runtime methods and attributes

    Returns
    -------
        dict: The list of record outputs which contain key, value, and optional description
    """
    global app_config
    global state_bucket_name
    global s3_resource_client

    try:
        __validate_event(event)

        if not app_config:
            app_config = Configuration()
            if not state_bucket_name:
                state_bucket_name = os.environ[STATE_BUCKET_NAME_KEY]
        if not s3_resource_client:
            s3_resource_client = boto3.resource('s3', config=app_config.get_boto_config())

        state_file_json_key = f'{event[AWS_ACCOUNT_ID_KEY]}/{event[PROVISIONED_PRODUCT_ID_KEY]}'
        state_file_content = __fetch_state_file_from_s3(state_bucket_name, state_file_json_key)
        record_outputs = __parse_outputs_from_state_file(state_file_content)

        response = {RECORD_OUTPUTS_KEY: record_outputs}
        log.info(f'Returning {response}')
        return response

    except Exception as e:
            log_exception(e)
            raise e

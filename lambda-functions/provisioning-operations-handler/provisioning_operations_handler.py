import os
import traceback
import json
import logging
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError


log = logging.getLogger()
log.setLevel(logging.INFO)

step_functions_client = None

# Environment variables
AWS_REGION_KEY: str = 'AWS_REGION'
STATE_MACHINE_ARN_KEY: str = 'STATE_MACHINE_ARN'
# Payload constants
RECORDS_KEY: str = 'Records'
BODY_KEY: str = 'body'
MESSAGE_ID_KEY: str = 'messageId'
TOKEN_KEY: str = 'token'
PROVISIONED_PRODUCT_ID_KEY: str = 'provisionedProductId'
RECORD_ID_KEY: str = 'recordId'
# Step Functions constants
EXECUTION_ARN_KEY: str = 'executionArn'
REQUEST_ID_KEY: str = 'RequestId'
RESPONSE_METADATA_KEY: str = 'ResponseMetadata'
ERROR_KEY: str = 'Error'
CODE_KEY: str = 'Code'
# Return object constants
BATCH_ITEM_FAILURES_KEY: str = 'batchItemFailures'
ITEM_IDENTIFIER_KEY: str = 'itemIdentifier'
# Step functions Error Codes
EXECUTION_ALREADY_EXISTS: str = 'ExecutionAlreadyExists'


def __start_state_machine(record: dict, state_machine_arn: str):
    state_machine_payload: dict = json.loads(record[BODY_KEY])

    # These fields are required to start the state machine execution.
    # Raise a KeyError if any are missing.
    token: str = state_machine_payload[TOKEN_KEY]
    provisioned_product_id: str = state_machine_payload[PROVISIONED_PRODUCT_ID_KEY]
    record_id: str = state_machine_payload[RECORD_ID_KEY]
    execution_name = f'{provisioned_product_id}-{record_id}'

    log.info(f'Starting state machine {state_machine_arn} with token {token} & name: {execution_name} & payload: {state_machine_payload}')

    start_execution_response = step_functions_client.start_execution(
        stateMachineArn=state_machine_arn,
        name=execution_name,
        input=json.dumps(state_machine_payload)
    )

    execution_arn: str = start_execution_response[EXECUTION_ARN_KEY]
    start_execution_request_id: str = start_execution_response[RESPONSE_METADATA_KEY][REQUEST_ID_KEY]

    log.info(f'Started state machine execution with arn: {execution_arn} for request Id: {start_execution_request_id}')


def handle_sqs_records(event, context):
    """
    Starts a state machine execution for each record in an SQS queue payload.
    The environment variable STATE_MACHINE_ARN must be set to indicate the state machine to execute.
    :param event: The SQS queue payload
    :param context: Lambda context
    :return: List of batch item failures
    """

    global step_functions_client
    if not step_functions_client:
        step_functions_client = boto3.client('stepfunctions', config=Config(
                region_name=os.environ.get(AWS_REGION_KEY),
                retries={
                    'max_attempts': 3,
                    'mode': 'standard'
                }))

    state_machine_arn: str = os.environ.get(STATE_MACHINE_ARN_KEY)
    records = event[RECORDS_KEY]
    log.info(f'Processing a total of: {len(records)} records')

    batchItemFailures = {BATCH_ITEM_FAILURES_KEY: []}
    for record in records:
        log.info(f'Processing record: {record}')
        try:
            __start_state_machine(record, state_machine_arn)
        except ClientError as clientError:
            error_code: str = clientError.response[ERROR_KEY][CODE_KEY]
            failing_request_id: str = clientError.response[RESPONSE_METADATA_KEY][REQUEST_ID_KEY]

            if error_code == EXECUTION_ALREADY_EXISTS:
                log.warning(f'A state machine execution with the same execution ARN '
                            f'already exists for requestId: {failing_request_id} & record {record}')
            else:
                log.error(f'Processing for record: {record} failed with error: {clientError} '
                          f'and requestId: {failing_request_id}')
                batchItemFailures[BATCH_ITEM_FAILURES_KEY].append({ITEM_IDENTIFIER_KEY: record[MESSAGE_ID_KEY]})

        except Exception as exception:
            log.error(f'Processing for {record} failed with error: {exception} & stack trace: {traceback.format_exc()}')
            batchItemFailures[BATCH_ITEM_FAILURES_KEY].append({ITEM_IDENTIFIER_KEY: record[MESSAGE_ID_KEY]})

    return batchItemFailures

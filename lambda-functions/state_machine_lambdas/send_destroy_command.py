import json
import logging
import os

from core.cli import create_runuser_command_with_default_user
from core.configuration import Configuration
from core.exception import log_exception
from core.ssm_facade import SsmFacade

log = logging.getLogger()
log.setLevel(logging.INFO)

# Globals
app_config = None
state_bucket_name = None
ssm_facade = None

# Constants
TERMINATE_PROVISIONED_PRODUCT = 'TERMINATE_PROVISIONED_PRODUCT'

# Input keys
INSTANCE_ID_KEY = 'instanceId'
OPERATION_KEY = "operation"
PROVISIONED_PRODUCT_ID_KEY = 'provisionedProductId'
AWS_ACCOUNT_ID_KEY = "awsAccountId"
LAUNCH_ROLE_ARN_KEY = 'launchRoleArn'

# Output keys
COMMAND_ID_KEY = 'commandId'

# Environment variable keys
STATE_BUCKET_NAME_KEY = 'STATE_BUCKET_NAME'


def __validate_event(event: dict):
    """Validates that all required fields are in the Lambda event and have expected values

    Parameters
    ----------
    event: dict, required
        The Lambda event to be validated
    """

    if INSTANCE_ID_KEY not in event:
        raise RuntimeError(f'{INSTANCE_ID_KEY} must be provided')
    if OPERATION_KEY not in event:
        raise RuntimeError(f'{OPERATION_KEY} must be provided')
    if event[OPERATION_KEY] != TERMINATE_PROVISIONED_PRODUCT:
        raise RuntimeError(f"{OPERATION_KEY} must be {TERMINATE_PROVISIONED_PRODUCT} but was {event[OPERATION_KEY]}")
    if PROVISIONED_PRODUCT_ID_KEY not in event:
        raise RuntimeError(f'{PROVISIONED_PRODUCT_ID_KEY} must be provided')
    if AWS_ACCOUNT_ID_KEY not in event:
        raise RuntimeError(f'{AWS_ACCOUNT_ID_KEY} must be provided')
    if LAUNCH_ROLE_ARN_KEY not in event:
        raise RuntimeError(f'{LAUNCH_ROLE_ARN_KEY} must be provided')


def __get_command_text(event: dict) -> str:
    """Creates the command to run on the instance based on the Lambda input event.

    Parameters
    ----------
    event: dict, required
        The input event to the Lambda function

    Returns
    -------
        str: The command text
    """

    base_command = f"""python3 -m terraform_runner --action=destroy \
    --provisioned-product-descriptor={f'{event[AWS_ACCOUNT_ID_KEY]}/{event[PROVISIONED_PRODUCT_ID_KEY]}'} \
    --launch-role={event[LAUNCH_ROLE_ARN_KEY]} \
    --region={app_config.get_region()} \
    --terraform-state-bucket={state_bucket_name}"""
    return create_runuser_command_with_default_user(base_command)

def send(event, context) -> dict:
    """Lambda handler to send a command to a host to run Terraform destroy

    Parameters
    ----------
    event: dict, required
        The input event to the Lambda function

    context: object, required
        Lambda Context runtime methods and attributes

    Returns
    -------
        dict: The command ID returned by SSM
    """
    log.info(f'Handling event: {event}')
    global app_config
    global state_bucket_name
    global ssm_facade

    try:
        __validate_event(event)

        if not app_config:
            app_config = Configuration()
        if not state_bucket_name:
            state_bucket_name = os.environ[STATE_BUCKET_NAME_KEY]
        if not ssm_facade:
            ssm_facade = SsmFacade(app_config)

        command_text = __get_command_text(event)

        response = {
            COMMAND_ID_KEY: ssm_facade.send_shell_command(command_text, event[INSTANCE_ID_KEY])
        }
        log.info(f'Returning {response}')
        return response

    except Exception as e:
        log_exception(e)
        raise e

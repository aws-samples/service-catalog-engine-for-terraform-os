import json
import logging
import os

from core.cli import create_runuser_command_with_default_user, escape_quotes_backslashes
from core.configuration import Configuration
from core.exception import log_exception
from core.ssm_facade import SsmFacade

log = logging.getLogger()
log.setLevel(logging.INFO)

# Globals
app_config = None
state_bucket_name = None
ssm_facade = None


#Constants
PROVISION_PRODUCT = 'PROVISION_PRODUCT'
UPDATE_PROVISIONED_PRODUCT = 'UPDATE_PROVISIONED_PRODUCT'

# Input keys
INSTANCE_ID_KEY = 'instanceId'
OPERATION_KEY = "operation"
PROVISIONED_PRODUCT_ID_KEY = 'provisionedProductId'
AWS_ACCOUNT_ID_KEY = "awsAccountId"
ARTIFACT_PATH_KEY = 'artifactPath'
ARTIFACT_TYPE_KEY = 'artifactType'
LAUNCH_ROLE_ARN_KEY = 'launchRoleArn'
PARAMETERS_KEY = 'parameters'
TRACER_TAG_KEY = 'tracerTag'
TAGS_KEY = 'tags'
TAG_KEY_KEY = 'key'
TAG_VALUE_KEY = 'value'

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
    if event[OPERATION_KEY] not in [PROVISION_PRODUCT, UPDATE_PROVISIONED_PRODUCT]:
        raise RuntimeError(f'{OPERATION_KEY} is invalid: {event[OPERATION_KEY]}')
    if PROVISIONED_PRODUCT_ID_KEY not in event:
        raise RuntimeError(f'{PROVISIONED_PRODUCT_ID_KEY} must be provided')
    if AWS_ACCOUNT_ID_KEY not in event:
        raise RuntimeError(f'{AWS_ACCOUNT_ID_KEY} must be provided')
    if ARTIFACT_PATH_KEY not in event:
        raise RuntimeError(f'{ARTIFACT_PATH_KEY} must be provided')
    if ARTIFACT_TYPE_KEY not in event:
        raise RuntimeError(f'{ARTIFACT_TYPE_KEY} must be provided')
    if LAUNCH_ROLE_ARN_KEY not in event:
        raise RuntimeError(f'{LAUNCH_ROLE_ARN_KEY} must be provided')
    if TRACER_TAG_KEY not in event:
        raise RuntimeError(f'{TRACER_TAG_KEY} must be provided')
    if TAG_KEY_KEY not in event[TRACER_TAG_KEY]:
        raise RuntimeError(f'{TRACER_TAG_KEY} must include {TAG_KEY_KEY}')
    if TAG_VALUE_KEY not in event[TRACER_TAG_KEY]:
        raise RuntimeError(f'{TRACER_TAG_KEY} must include {TAG_VALUE_KEY}')


def __get_optional_json(body, key) -> str:
    """Gets an optional entry from a dict and returns a valid json string representing the result

    Parameters
    ----------
    body: dict, required
        The dict where the key may or may not be found

    key: str, required
        The key to look up in the dict

    Returns
    -------
        str: Json form of the key-value pair if it exists; otherwise an empty json string.
    """

    try:
        return json.dumps(body[key])
    except KeyError:
        # If the optional key is not found, return an empty json string
        return '{}'

def __get_tags_text(event: dict) -> str:
    """Creates the text for the tags parameter for the command.

    Parameters
    ----------
    event: dict, required
        The input event to the Lambda function

    Returns
    -------
        str: The text for the command's tags argument
    """
    total_tags = [event[TRACER_TAG_KEY]]
    if TAGS_KEY in event:
        total_tags += event[TAGS_KEY]
    return escape_quotes_backslashes(json.dumps(total_tags))

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
    artifact_parameters_text = escape_quotes_backslashes(__get_optional_json(event, PARAMETERS_KEY))
    tags_text = __get_tags_text(event)

    base_command = f"""python3 -m terraform_runner --action=apply \
    --provisioned-product-descriptor={f'{event[AWS_ACCOUNT_ID_KEY]}/{event[PROVISIONED_PRODUCT_ID_KEY]}'} \
    --launch-role={event[LAUNCH_ROLE_ARN_KEY]} \
    --artifact-path={event[ARTIFACT_PATH_KEY]} \
    --region={app_config.get_region()} \
    --terraform-state-bucket={state_bucket_name} \
    --artifact-parameters="{artifact_parameters_text}" \
    --tags="{tags_text}" """
    return create_runuser_command_with_default_user(base_command)

def send(event, context) -> dict:
    """Lambda handler to send a command to a host to run Terraform apply

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

        log.info(f'Sending command text {command_text}')

        response = {
            COMMAND_ID_KEY: ssm_facade.send_shell_command(command_text, event[INSTANCE_ID_KEY])
        }
        log.info(f'Returning {response}')
        return response

    except Exception as e:
        log_exception(e)
        raise e

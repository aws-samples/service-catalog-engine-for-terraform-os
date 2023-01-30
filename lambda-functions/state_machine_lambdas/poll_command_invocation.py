import logging

from core.configuration import Configuration
from core.exception import log_exception
from core.ssm_facade import SsmFacade


# PollCommandInvocationFunction input keys
COMMAND_ID_KEY = 'commandId'
INSTANCE_ID_KEY = 'instanceId'


log = logging.getLogger()
log.setLevel(logging.INFO)

# Globals
app_config = None
ssm_facade = None


def __validate_event(event):
    """Raises an exception if any required entries are missing from the Lambda event"""
    if COMMAND_ID_KEY not in event:
        raise RuntimeError(f'{COMMAND_ID_KEY} must be provided')
    if INSTANCE_ID_KEY not in event:
        raise RuntimeError(f'{INSTANCE_ID_KEY} must be provided')


def poll(event, context) -> dict:
    """Lambda function to poll the status of a command invocation from Systems Manager

    Parameters
    ----------
    event: dict, required
        The input event to the Lambda function
        - CommandId(Required): The parent command ID of the invocation plugin.
        - InstanceId(Required): The ID of the managed node targeted by the command.

    context: object, required
        Lambda Context runtime methods and attributes

    Returns
    ------
        dict
        - InvocationStatus: Status of invocation plugin in the selected EC2 instance
    """

    global app_config
    global ssm_facade

    try:
        __validate_event(event)

        command_id = event[COMMAND_ID_KEY]
        instance_id = event[INSTANCE_ID_KEY]

        if not app_config:
            app_config = Configuration()
        if not ssm_facade:
            ssm_facade = SsmFacade(app_config)

        response = ssm_facade.get_command_invocation(command_id, instance_id)
        log.info(f'Returning {response}')
        return response

    except Exception as e:
        log_exception(e)
        raise e

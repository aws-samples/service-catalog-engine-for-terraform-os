import logging

import boto3

from core.configuration import Configuration

log = logging.getLogger()
log.setLevel(logging.INFO)


# Constants
DOCUMENT_NAME_RUN_SHELL_COMMAND = "AWS-RunShellScript"

# SSM response KEYS
COMMAND_KEY = 'Command'
COMMAND_ID_KEY = 'CommandId'
STATUS_KEY = 'Status'
STANDARD_ERROR_CONTENT_KEY = 'StandardErrorContent'

# Function output keys
INVOCATION_STATUS_KEY = 'invocationStatus'
ERROR_MESSAGE_KEY = 'errorMessage'


class SsmFacade:

    def __init__(self, app_config: Configuration):
        self.__ssm_client = boto3.client('ssm', config = app_config.get_boto_config())

    def send_shell_command(self, command_text: str, instance_id:     str) -> str:
        """Uses SSM to run a shell command on an instance

        Parameters
        ----------
        command_text: str, required
            The shell command to run

        instance_id: str, required
            The instance ID of the host where the command will be run

        Returns
        -------
            str: The command ID of the command that was started
        """
        log.info(f'Sending shell command to instance {instance_id}: {command_text}')

        response = self.__ssm_client.send_command(
            InstanceIds=[instance_id],
            DocumentName=DOCUMENT_NAME_RUN_SHELL_COMMAND,
            Parameters={'commands': [command_text]},
            CloudWatchOutputConfig={'CloudWatchOutputEnabled': True})
        log.info(f'SendCommand response: {response}')
        return response[COMMAND_KEY][COMMAND_ID_KEY]

    def get_command_invocation(self, command_id: str, instance_id: str) -> dict:
        """Uses SSM to run get a command invocation

        Parameters
        ----------
        command_id: str, required
            The command ID of the command invocation

        instance_id: str, required
            The instance ID where the command was run

        Returns
        -------
            dict: Contains elements from the SSM response.
                Keys included are invocationStatus and errorMessage
        """
        log.info(f'Get command invocation for command ID {command_id} & instance ID {instance_id}')

        get_command_invocation_response = self.__ssm_client.get_command_invocation(
            CommandId=command_id,
            InstanceId=instance_id
        )

        response = {
            INVOCATION_STATUS_KEY: get_command_invocation_response[STATUS_KEY],
            ERROR_MESSAGE_KEY: get_command_invocation_response[STANDARD_ERROR_CONTENT_KEY]
        }
        return response

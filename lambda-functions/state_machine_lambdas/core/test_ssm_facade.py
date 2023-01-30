import json
from unittest import main, TestCase
from unittest.mock import MagicMock, Mock, patch

from botocore.exceptions import ClientError

from core.ssm_facade import SsmFacade, DOCUMENT_NAME_RUN_SHELL_COMMAND


class TestSsmFacade(TestCase):

    @patch('boto3.client')
    def test_send_shell_command_happy_path(self: TestCase,
                             mocked_client: MagicMock):
        # arrange
        mocked_app_config = Mock()
        mocked_boto_config = Mock()
        mocked_app_config.get_boto_config.return_value = mocked_boto_config

        send_command_response = {'Command': {'CommandId': 'commandId'}}
        mocked_client.return_value.send_command.return_value = send_command_response

        command_text = 'command-text'
        instance_id = 'instance-id'
        facade = SsmFacade(mocked_app_config)

        # act
        function_response = facade.send_shell_command(command_text, instance_id)

        # assert
        mocked_client.assert_called_once_with('ssm', config=mocked_boto_config)
        mocked_client.return_value.send_command.assert_called_once_with(
            InstanceIds=[instance_id],
            DocumentName=DOCUMENT_NAME_RUN_SHELL_COMMAND,
            Parameters={'commands': [command_text]},
            CloudWatchOutputConfig={'CloudWatchOutputEnabled': True})
        self.assertEqual(function_response, 'commandId')

    @patch('boto3.client')
    def test_send_shell_command_raises_client_error(self: TestCase,
                             mocked_client: MagicMock):
        # arrange
        mocked_app_config = Mock()
        mocked_boto_config = Mock()
        mocked_app_config.get_boto_config.return_value = mocked_boto_config

        mocked_error_response = {
            'Error': {
                'Message': 'Some SSM 4XX or 5XX error'
            },
            'ResponseMetadata': {
                'RequestId': 'some-random-uuid'
            }
        }
        mocked_client.return_value.send_command.side_effect = ClientError(
            operation_name='SendCommand',
            error_response=mocked_error_response
        )


        command_text = 'command-text'
        instance_id = 'instance-id'
        facade = SsmFacade(mocked_app_config)

        # act
        with self.assertRaises(ClientError) as context:
            facade.send_shell_command(command_text, instance_id)

        # assert
        mocked_client.assert_called_once_with('ssm', config=mocked_boto_config)
        mocked_client.return_value.send_command.assert_called_once_with(
            InstanceIds=[instance_id],
            DocumentName=DOCUMENT_NAME_RUN_SHELL_COMMAND,
            Parameters={'commands': [command_text]},
            CloudWatchOutputConfig={'CloudWatchOutputEnabled': True})
        self.assertEqual(context.expected, ClientError)
        self.assertEqual(context.exception.response, mocked_error_response)

    @patch('boto3.client')
    def test_get_command_invocation_happy_path(self: TestCase,
                                                mocked_client: MagicMock):
        # Act
        mocked_app_config = Mock()
        mocked_boto_config = Mock()
        mocked_app_config.get_boto_config.return_value = mocked_boto_config

        command_id = "fc7b5795-aab1-43a8-9fa0-8645409091fe"
        instance_id = "i-0c9a068586ae5c597"

        ssm_client_response = {
            "Comment": "",
            "ExecutionElapsedTime": "PT0.102S",
            "ExecutionEndDateTime": "2022-11-17T21:41:16.561Z",
            "StandardErrorContent": "",
            "CloudWatchOutputConfig": {
                "CloudWatchLogGroupName": "Dummy",
                "CloudWatchOutputEnabled": True
            },
            "InstanceId": instance_id,
            "DocumentName": "AWS-RunShellScript",
            "DocumentVersion": "1",
            "Status": "Success",
            "StatusDetails": "Success",
            "PluginName": "aws:runShellScript",
            "StandardOutputContent": "/usr/bin\n",
            "ResponseCode": 0,
            "ExecutionStartDateTime": "2022-11-17T21:41:16.561Z",
            "CommandId": command_id
        }
        mocked_ssm_client: MagicMock = mocked_client.return_value
        mocked_ssm_client.get_command_invocation.return_value = ssm_client_response
        facade = SsmFacade(mocked_app_config)

        # Act
        response = facade.get_command_invocation(command_id, instance_id)

        # Assert
        mocked_client.assert_called_once_with('ssm', config=mocked_app_config.get_boto_config())
        mocked_ssm_client.get_command_invocation.assert_called_once_with(
            CommandId=command_id,
            InstanceId=instance_id
        )

        self.assertEqual(response, {'invocationStatus': 'Success', 'errorMessage': ''})

    @patch('boto3.client')
    def test_get_command_invocation_given_ssm_error(self: TestCase,
                                                     mocked_client: MagicMock):
        # Arrange
        mocked_app_config = Mock()
        mocked_boto_config = Mock()
        mocked_app_config.get_boto_config.return_value = mocked_boto_config

        command_id = "fc7b5795-aab1-43a8-9fa0-8645409091fe"
        instance_id = "i-0c9a068586ae5c597"

        error_response = {
            'Error': {
                'Message': 'Some SSM 4XX or 5XX error'
            },
            'ResponseMetadata': {
                'RequestId': 'some-random-uuid'
            }
        }

        mocked_ssm_client: MagicMock = mocked_client.return_value
        mocked_ssm_client.get_command_invocation.side_effect = ClientError(
            operation_name='get_command_invocation',
            error_response=error_response
        )
        facade = SsmFacade(mocked_app_config)

        # Act
        with self.assertRaises(ClientError) as context:
            facade.get_command_invocation(command_id, instance_id)

        # Assert
        mocked_client.assert_called_once_with('ssm', config=mocked_app_config.get_boto_config())
        mocked_ssm_client.get_command_invocation.assert_called_once_with(
            CommandId=command_id,
            InstanceId=instance_id
        )

        self.assertEqual(context.expected, ClientError)
        self.assertEqual(context.exception.response, error_response)


if __name__ == '__main__':
    main()

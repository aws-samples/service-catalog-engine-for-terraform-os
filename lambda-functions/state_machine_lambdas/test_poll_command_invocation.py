from unittest import main, TestCase
from unittest.mock import patch, MagicMock

from botocore.exceptions import ClientError

import poll_command_invocation


class TestPollCommandInvocation(TestCase):

    def setUp(self):
        # This is required to reset the mocks
        poll_command_invocation.app_config = None
        poll_command_invocation.ssm_facade = None

    @patch('poll_command_invocation.Configuration')
    @patch('poll_command_invocation.ssm_facade')
    def test_poll_command_invocation_happy_path(self: TestCase,
                                                mocked_ssm_facade: MagicMock,
                                                mocked_configuration: MagicMock):
        #Arrange
        event = {
            "commandId": "fc7b5795-aab1-43a8-9fa0-8645409091fe",
            "instanceId": "i-0c9a068586ae5c597"
        }
        mocked_response = {
            "errorMessage": "",
            "invocationStatus": "Success"
        }
        mocked_app_config = mocked_configuration.return_value
        mocked_ssm_facade.get_command_invocation.return_value = mocked_response

        # Act
        response = poll_command_invocation.poll(event, None)

        # Assert
        mocked_configuration.assert_called_once()
        mocked_ssm_facade.get_command_invocation.assert_called_once_with(event['commandId'], event['instanceId'])
        self.assertEqual(response, {'invocationStatus': 'Success', 'errorMessage': ''})

    @patch('poll_command_invocation.Configuration')
    @patch('poll_command_invocation.ssm_facade')
    def test_poll_command_invocation_given_ssm_error(self: TestCase,
                                                     mocked_ssm_facade: MagicMock,
                                                     mocked_configuration: MagicMock):
        # Arrange
        event = {
            "commandId": "fc7b5795-aab1-43a8-9fa0-8645409091fe",
            "instanceId": "i-0c9a068586ae5c597"
        }

        error_response = {
            'Error': {
                'Message': 'Some SSM 4XX or 5XX error'
            },
            'ResponseMetadata': {
                'RequestId': 'some-random-uuid'
            }
        }

        mocked_app_config = mocked_configuration.return_value
        mocked_ssm_facade.get_command_invocation.side_effect = ClientError(
            operation_name='get_command_invocation',
            error_response=error_response
        )

        # Act
        with self.assertRaises(ClientError) as context:
            poll_command_invocation.poll(event, None)

        # Assert
        mocked_configuration.assert_called_once()
        mocked_ssm_facade.get_command_invocation.assert_called_once_with(event['commandId'], event['instanceId'])

        self.assertEqual(context.expected, ClientError)
        self.assertEqual(context.exception.response, error_response)

    @patch('poll_command_invocation.Configuration')
    @patch('poll_command_invocation.ssm_facade')
    def test_poll_command_invocation_command_id_not_given_throw_RuntimeError(self: TestCase,
                                                                             mocked_ssm_facade: MagicMock,
                                                                             mocked_configuration: MagicMock):
        event = {
            "instanceId": "i-0c9a068586ae5c597"
        }
        mocked_app_config = mocked_configuration.return_value

        with self.assertRaises(RuntimeError) as context:
            poll_command_invocation.poll(event, None)

        mocked_configuration.assert_not_called()
        mocked_ssm_facade.assert_not_called()

        self.assertEqual(context.expected, RuntimeError)
        self.assertEqual(str(context.exception), "commandId must be provided")

    @patch('poll_command_invocation.Configuration')
    @patch('poll_command_invocation.ssm_facade')
    def test_poll_command_invocation_instance_id_not_given_throw_RuntimeError(self: TestCase,
                                                                              mocked_ssm_facade: MagicMock,
                                                                              mocked_configuration: MagicMock):
        event = {
            "commandId": "fc7b5795-aab1-43a8-9fa0-8645409091fe"
        }
        mocked_app_config = mocked_configuration.return_value

        with self.assertRaises(RuntimeError) as context:
            poll_command_invocation.poll(event, None)

        mocked_configuration.assert_not_called()
        mocked_ssm_facade.assert_not_called()

        self.assertEqual(context.expected, RuntimeError)
        self.assertEqual(str(context.exception), "instanceId must be provided")


if __name__ == '__main__':
    main()

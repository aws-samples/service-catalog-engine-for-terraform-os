import json
from unittest import main, TestCase
from unittest.mock import MagicMock, Mock, patch

from botocore.exceptions import ClientError

import send_destroy_command


class TestSendDestroyCommand(TestCase):

    def setUp(self: TestCase):
        # This is required to reset the mocks
        send_destroy_command.app_config = None
        send_destroy_command.ssm_facade = None

    @patch('send_destroy_command.Configuration')
    @patch('send_destroy_command.os')
    @patch('send_destroy_command.ssm_facade')
    def test_send_happy_path(self: TestCase,
                             mocked_ssm_facade: MagicMock,
                             mocked_os: MagicMock,
                             mocked_configuration: MagicMock):
        # arrange
        state_bucket_name = 'state-bucket-name'
        mocked_os.environ.__getitem__.return_value = state_bucket_name
        mocked_app_config = Mock()
        mocked_app_config.get_region.return_value = 'us-east-1'
        mocked_configuration.return_value = mocked_app_config
        mocked_ssm_facade.send_shell_command.return_value = 'command-id'

        mocked_event = {
            "instanceId": "instance-id",
            "operation": "TERMINATE_PROVISIONED_PRODUCT",
            "provisionedProductId": "pp-id",
            "awsAccountId": "account-Id",
            "provisionedProductName": "pp-name",
            "recordId": "rec-id",
            "launchRoleArn": 'launch-role-arn',
        }

        # The indents here are weird because it needs to match the actual command including whitespace.
        expected_command_text = f"""runuser -l ec2-user -c 'python3 -m terraform_runner --action=destroy \
    --provisioned-product-descriptor={mocked_event['awsAccountId'] + '/' + mocked_event['provisionedProductId']} \
    --launch-role={mocked_event['launchRoleArn']} \
    --region={mocked_app_config.get_region()} \
    --terraform-state-bucket={state_bucket_name}'"""

        # act
        function_response = send_destroy_command.send(mocked_event, None)

        # assert
        mocked_configuration.assert_called_once()
        mocked_ssm_facade.send_shell_command.assert_called_once_with(expected_command_text, 'instance-id')
        self.assertEqual(function_response, {'commandId': 'command-id'})

    @patch('send_destroy_command.Configuration')
    @patch('send_destroy_command.os')
    @patch('send_destroy_command.ssm_facade')
    def test_send_ssm_client_error(self: TestCase,
                                   mocked_ssm_facade: MagicMock,
                                   mocked_os: MagicMock,
                                   mocked_configuration: MagicMock):
        # arrange
        state_bucket_name = 'state-bucket-name'
        mocked_os.environ.__getitem__.return_value = state_bucket_name
        mocked_error_response = {
            'Error': {
                'Message': 'Some SSM 4XX or 5XX error'
            },
            'ResponseMetadata': {
                'RequestId': 'some-random-uuid'
            }
        }
        mocked_ssm_facade.send_shell_command.side_effect = ClientError(
            operation_name='SendCommand',
            error_response=mocked_error_response
        )

        mocked_app_config = Mock()
        mocked_app_config.get_region.return_value = 'us-east-1'
        mocked_configuration.return_value = mocked_app_config

        mocked_event = {
            "instanceId": "instanceId",
            "operation": "TERMINATE_PROVISIONED_PRODUCT",
            "provisionedProductId": "pp-id",
            "awsAccountId": "account-Id",
            "provisionedProductName": "pp-name",
            "recordId": "rec-id",
            "launchRoleArn": "launch-role-arn",
        }

        # The indents here are weird because it needs to match the actual command including whitespace.
        expected_command_text = f"""runuser -l ec2-user -c 'python3 -m terraform_runner --action=destroy \
    --provisioned-product-descriptor={mocked_event['awsAccountId'] + '/' + mocked_event['provisionedProductId']} \
    --launch-role={mocked_event['launchRoleArn']} \
    --region={mocked_app_config.get_region()} \
    --terraform-state-bucket={state_bucket_name}'"""

        # act
        with self.assertRaises(ClientError) as context:
            send_destroy_command.send(mocked_event, None)

        # assert
        mocked_configuration.assert_called_once()
        mocked_ssm_facade.send_shell_command.assert_called_once_with(expected_command_text, 'instanceId')
        self.assertEqual(context.expected, ClientError)
        self.assertEqual(context.exception.response, mocked_error_response)

    def test_send_missing_operation(self: TestCase):
        # arrange
        mocked_event = {
            "instanceId": "instance-id",
            "provisionedProductId": "pp-id",
            "provisionedProductName": "pp-name",
            "recordId": "rec-id",
            "launchRoleArn": "arn",
        }

        # act
        with self.assertRaises(RuntimeError) as context:
            send_destroy_command.send(mocked_event, None)

        # assert
        self.assertEqual(context.expected, RuntimeError)
        self.assertEqual(str(context.exception), "operation must be provided")

    def test_send_invalid_operation(self: TestCase):
        # arrange
        mocked_event = {
            "instanceId": "instance-id",
            "operation": "invalid-operation",
            "provisionedProductId": "pp-id",
            "awsAccountId": "account-Id",
            "provisionedProductName": "pp-name",
            "recordId": "rec-id",
            "launchRoleArn": "arn",
        }

        # act
        with self.assertRaises(RuntimeError) as context:
            send_destroy_command.send(mocked_event, None)

        # assert
        self.assertEqual(context.expected, RuntimeError)
        self.assertEqual(str(context.exception), f"operation must be TERMINATE_PROVISIONED_PRODUCT but was {mocked_event['operation']}")

    def test_send_missing_provisioned_product_id(self: TestCase):
        # arrange
        mocked_event = {
            "instanceId": "instance-id",
            "operation": "TERMINATE_PROVISIONED_PRODUCT",
            "awsAccountId": "account-Id",
            "provisionedProductName": "pp-name",
            "recordId": "rec-id",
            "launchRoleArn": "arn",
        }

        # act
        with self.assertRaises(RuntimeError) as context:
            send_destroy_command.send(mocked_event, None)

        # assert
        self.assertEqual(context.expected, RuntimeError)
        self.assertEqual(str(context.exception), "provisionedProductId must be provided")

    def test_send_missing_instance_id(self: TestCase):
        # arrange
        mocked_event = {
            "operation": "TERMINATE_PROVISIONED_PRODUCT",
            "provisionedProductId": "pp-id",
            "awsAccountId": "account-Id",
            "provisionedProductName": "pp-name",
            "recordId": "rec-id",
            "launchRoleArn": "arn",
        }

        # act
        with self.assertRaises(RuntimeError) as context:
            send_destroy_command.send(mocked_event, None)

        # assert
        self.assertEqual(context.expected, RuntimeError)
        self.assertEqual(str(context.exception), "instanceId must be provided")

    def test_send_missing_launch_role(self: TestCase):
        # arrange
        mocked_event = {
            "instanceId": "instance-id",
            "operation": "TERMINATE_PROVISIONED_PRODUCT",
            "provisionedProductId": "pp-id",
            "awsAccountId": "account-Id",
            "provisionedProductName": "pp-name",
        }

        # act
        with self.assertRaises(RuntimeError) as context:
            send_destroy_command.send(mocked_event, None)

        # assert
        self.assertEqual(context.expected, RuntimeError)
        self.assertEqual(str(context.exception), "launchRoleArn must be provided")

    def test_send_missing_aws_account_id(self: TestCase):
        # arrange
        mocked_event = {
            "instanceId": "instance-id",
            "operation": "TERMINATE_PROVISIONED_PRODUCT",
            "provisionedProductId": "pp-id",
            "provisionedProductName": "pp-name",
            "recordId": "rec-id",
            "launchRoleArn": "arn"
        }

        # act
        with self.assertRaises(RuntimeError) as context:
            send_destroy_command.send(mocked_event, None)

        # assert
        self.assertEqual(context.expected, RuntimeError)
        self.assertEqual(str(context.exception), "awsAccountId must be provided")

if __name__ == '__main__':
    main()

import json
from unittest import main, TestCase
from unittest.mock import MagicMock, Mock, patch

from botocore.exceptions import ClientError

import send_apply_command


class TestSendApplyCommand(TestCase):

    def setUp(self: TestCase):
        # This is required to reset the mocks
        send_apply_command.app_config = None
        send_apply_command.ssm_facade = None

    @patch('send_apply_command.Configuration')
    @patch('send_apply_command.os')
    @patch('send_apply_command.ssm_facade')
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

        parameter_key = 'parameter-key'
        parameter_value = 'parameter-value'
        tracer_tag_key = "TRACER_TAG_DO_NOT_DELETE"
        tracer_tag_value = 'pp-id'
        tag_key1 = 'tag-key1'
        tag_value1 = 'tag-value1'
        tag_key2 = 'tag-key2'
        tag_value2 = 'tag-value2'

        mocked_event = {
            "instanceId": "instance-id",
            "tracerTag": {
                "key": tracer_tag_key,
                "value": tracer_tag_value
            },
            "operation": "PROVISION_PRODUCT",
            "provisionedProductId": "pp-id",
            "awsAccountId": "account-id",
            "provisionedProductName": "pp-name",
            "recordId": "rec-id",
            "launchRoleArn": 'launch-role-arn',
            "artifactPath": "artifact-path",
            "artifactType": "AWS_S3",
            "parameters": [
                {
                    "key": parameter_key,
                    "value": parameter_value
                }
            ],
            "tags": [
                {
                    "key": tag_key1,
                    "value": tag_value1
                },
                {
                    "key": tag_key2,
                    "value": tag_value2
                }
            ]
        }

        parameters_list = f'[{{\\"key\\": \\"{parameter_key}\\", \\"value\\": \\"{parameter_value}\\"}}]'
        tags_list = f'[{{\\"key\\": \\"{tracer_tag_key}\\", \\"value\\": \\"{tracer_tag_value}\\"}}, {{\\"key\\": \\"{tag_key1}\\", \\"value\\": \\"{tag_value1}\\"}}, {{\\"key\\": \\"{tag_key2}\\", \\"value\\": \\"{tag_value2}\\"}}]'

        # The indents here are weird because it needs to match the actual command including whitespace.
        expected_command_text = f"""runuser -l ec2-user -c 'python3 -m terraform_runner --action=apply \
    --provisioned-product-descriptor={mocked_event['awsAccountId'] + '/' + mocked_event['provisionedProductId']} \
    --launch-role={mocked_event['launchRoleArn']} \
    --artifact-path={mocked_event['artifactPath']} \
    --region=us-east-1 \
    --terraform-state-bucket=state-bucket-name \
    --artifact-parameters="{parameters_list}" \
    --tags="{tags_list}" '"""

        # act
        function_response = send_apply_command.send(mocked_event, None)

        # assert
        mocked_configuration.assert_called_once()
        mocked_ssm_facade.send_shell_command.assert_called_once_with(expected_command_text, 'instance-id')
        self.assertEqual(function_response, {'commandId': 'command-id'})

    @patch('send_apply_command.Configuration')
    @patch('send_apply_command.os')
    @patch('send_apply_command.ssm_facade')
    def test_send_with_complex_parameters_happy_path(self: TestCase,
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

        tracer_tag_key = "TRACER_TAG_DO_NOT_DELETE"
        tracer_tag_value = 'pp-id'

        mocked_event = {
            "instanceId": "instance-id",
            "tracerTag": {
                "key": tracer_tag_key,
                "value": tracer_tag_value
            },
            "operation": "PROVISION_PRODUCT",
            "provisionedProductId": "pp-id",
            "awsAccountId": "account-id",
            "provisionedProductName": "pp-name",
            "recordId": "rec-id",
            "launchRoleArn": 'launch-role-arn',
            "artifactPath": "artifact-path",
            "artifactType": "AWS_S3",
            "parameters": [
                {
                    "key": "aws_amis",
                    "value": "{\"us-east-1\":\"ami-5f709f34\",\"us-west-2\":\"ami-7f675e4f\"}"
                },
                {
                    "key": "aws_region",
                    "value": "us-east-1"
                },
                {
                    "key": "key_name",
                    "value": "test"
                }
            ]
        }

        parameters_list = '[{\\"key\\": \\"aws_amis\\", \\"value\\": \\"{\\\\\\"us-east-1\\\\\\":\\\\\\"ami-5f709f34\\\\\\",\\\\\\"us-west-2\\\\\\":\\\\\\"ami-7f675e4f\\\\\\"}\\"}, {\\"key\\": \\"aws_region\\", \\"value\\": \\"us-east-1\\"}, {\\"key\\": \\"key_name\\", \\"value\\": \\"test\\"}]'
        tags_list = f'[{{\\"key\\": \\"{tracer_tag_key}\\", \\"value\\": \\"{tracer_tag_value}\\"}}]'

        # The indents here are weird because it needs to match the actual command including whitespace.
        expected_command_text = f"""runuser -l ec2-user -c 'python3 -m terraform_runner --action=apply \
    --provisioned-product-descriptor={mocked_event['awsAccountId'] + '/' + mocked_event['provisionedProductId']} \
    --launch-role={mocked_event['launchRoleArn']} \
    --artifact-path={mocked_event['artifactPath']} \
    --region=us-east-1 \
    --terraform-state-bucket=state-bucket-name \
    --artifact-parameters="{parameters_list}" \
    --tags="{tags_list}" '"""

        # act
        function_response = send_apply_command.send(mocked_event, None)

        # assert
        mocked_configuration.assert_called_once()
        mocked_ssm_facade.send_shell_command.assert_called_once_with(expected_command_text, 'instance-id')
        self.assertEqual(function_response, {'commandId': 'command-id'})

    @patch('send_apply_command.Configuration')
    @patch('send_apply_command.os')
    @patch('send_apply_command.ssm_facade')
    def test_send_ssm_client_error(self: TestCase,
                                   mocked_ssm_facade: MagicMock,
                                   mocked_os: MagicMock,
                                   mocked_configuration: MagicMock):
        # arrange
        mocked_os.environ.__getitem__.return_value = 'state-bucket-name'
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

        parameter_key = 'parameter-key'
        parameter_value = 'parameter-value'
        tracer_tag_key = "TRACER_TAG_DO_NOT_DELETE"
        tracer_tag_value = 'pp-id'

        mocked_event = {
            "instanceId": "instance-id",
            "tracerTag": {
                "key": tracer_tag_key,
                "value": tracer_tag_value
            },
            "operation": "PROVISION_PRODUCT",
            "provisionedProductId": "pp-id",
            "awsAccountId": "account-id",
            "provisionedProductName": "pp-name",
            "recordId": "rec-id",
            "launchRoleArn": 'launch-role-arn',
            "artifactPath": "artifact-path.tar.gz",
            "artifactType": "AWS_S3",
            "parameters": [
                {
                    "key": parameter_key,
                    "value": parameter_value
                }
            ]
        }

        parameters_list = f'[{{\\"key\\": \\"{parameter_key}\\", \\"value\\": \\"{parameter_value}\\"}}]'
        tags_list = f'[{{\\"key\\": \\"{tracer_tag_key}\\", \\"value\\": \\"{tracer_tag_value}\\"}}]'

        # The indents here are weird because it needs to match the actual command including whitespace.
        expected_command_text = f"""runuser -l ec2-user -c 'python3 -m terraform_runner --action=apply \
    --provisioned-product-descriptor={mocked_event['awsAccountId'] + '/' + mocked_event['provisionedProductId']} \
    --launch-role={mocked_event['launchRoleArn']} \
    --artifact-path={mocked_event['artifactPath']} \
    --region=us-east-1 \
    --terraform-state-bucket=state-bucket-name \
    --artifact-parameters="{parameters_list}" \
    --tags="{tags_list}" '"""

        # act
        with self.assertRaises(ClientError) as context:
            send_apply_command.send(mocked_event, None)

        # assert
        mocked_configuration.assert_called_once()
        mocked_ssm_facade.send_shell_command.assert_called_once_with(expected_command_text, 'instance-id')
        self.assertEqual(context.expected, ClientError)
        self.assertEqual(context.exception.response, mocked_error_response)

    def test_send_missing_tracer_tag(self: TestCase):
        # arrange
        mocked_event = {
            "instanceId": "instance-id",
            "operation": "PROVISION_PRODUCT",
            "provisionedProductId": "pp-id",
            "awsAccountId": "account-id",
            "provisionedProductName": "pp-name",
            "recordId": "rec-id",
            "launchRoleArn": "launch-role-arn",
            "artifactPath": "artifact-path.tar.gz",
            "artifactType": "AWS_S3",
        }

        # act
        with self.assertRaises(RuntimeError) as context:
            send_apply_command.send(mocked_event, None)

        # assert
        self.assertEqual(context.expected, RuntimeError)
        self.assertEqual(str(context.exception), "tracerTag must be provided")

    def test_send_missing_tracer_tag_key(self: TestCase):
        # arrange
        mocked_event = {
            "instanceId": "instance-id",
            "operation": "PROVISION_PRODUCT",
            "tracerTag": {
                "value": "pp-foo"
            },
            "provisionedProductId": "pp-id",
            "awsAccountId": "account-id",
            "provisionedProductName": "pp-name",
            "recordId": "rec-id",
            "launchRoleArn": "launch-role-arn",
            "artifactPath": "artifact-path.tar.gz",
            "artifactType": "AWS_S3",
        }

        # act
        with self.assertRaises(RuntimeError) as context:
            send_apply_command.send(mocked_event, None)

        # assert
        self.assertEqual(context.expected, RuntimeError)
        self.assertEqual(str(context.exception), "tracerTag must include key")

    def test_send_missing_tracer_tag_value(self: TestCase):
        # arrange
        mocked_event = {
            "instanceId": "instance-id",
            "operation": "PROVISION_PRODUCT",
            "tracerTag": {
                "key": "TRACER_TAG_DO_NOT_DELETE"
            },
            "provisionedProductId": "pp-id",
            "awsAccountId": "account-id",
            "provisionedProductName": "pp-name",
            "recordId": "rec-id",
            "launchRoleArn": "launch-role-arn",
            "artifactPath": "artifact-path.tar.gz",
            "artifactType": "AWS_S3",
        }

        # act
        with self.assertRaises(RuntimeError) as context:
            send_apply_command.send(mocked_event, None)

        # assert
        self.assertEqual(context.expected, RuntimeError)
        self.assertEqual(str(context.exception), "tracerTag must include value")

    def test_send_missing_operation(self: TestCase):
        # arrange
        mocked_event = {
            "instanceId": "instance-id",
            "tracerTag": {
                "key": "TRACER_TAG_DO_NOT_DELETE",
                "value": "pp-foo"
            },
            "provisionedProductId": "pp-id",
            "awsAccountId": "account-id",
            "provisionedProductName": "pp-name",
            "recordId": "rec-id",
            "launchRoleArn": "arn",
            "artifactPath": "artifact-path.tar.gz",
            "artifactType": "AWS_S3",
        }

        # act
        with self.assertRaises(RuntimeError) as context:
            send_apply_command.send(mocked_event, None)

        # assert
        self.assertEqual(context.expected, RuntimeError)
        self.assertEqual(str(context.exception), "operation must be provided")

    def test_send_invalid_operation(self: TestCase):
        # arrange
        mocked_event = {
            "instanceId": "instance-id",
            "operation": "invalid-operation",
            "tracerTag": {
                "key": "TRACER_TAG_DO_NOT_DELETE",
                "value": "pp-foo"
            },
            "provisionedProductId": "pp-id",
            "awsAccountId": "account-id",
            "provisionedProductName": "pp-name",
            "recordId": "rec-id",
            "launchRoleArn": "arn",
            "artifactPath": "artifact-path.tar.gz",
            "artifactType": "AWS_S3",
        }

        # act
        with self.assertRaises(RuntimeError) as context:
            send_apply_command.send(mocked_event, None)

        # assert
        self.assertEqual(context.expected, RuntimeError)
        self.assertEqual(str(context.exception), f"operation is invalid: {mocked_event['operation']}")

    def test_send_missing_provisioned_product_id(self: TestCase):
        # arrange
        mocked_event = {
            "instanceId": "instance-id",
            "operation": "PROVISION_PRODUCT",
            "tracerTag": {
                "key": "TRACER_TAG_DO_NOT_DELETE",
                "value": "pp-foo"
            },
            "awsAccountId": "account-id",
            "provisionedProductName": "pp-name",
            "recordId": "rec-id",
            "launchRoleArn": "arn",
            "artifactPath": "artifact-path.tar.gz",
            "artifactType": "AWS_S3",
        }

        # act
        with self.assertRaises(RuntimeError) as context:
            send_apply_command.send(mocked_event, None)

        # assert
        self.assertEqual(context.expected, RuntimeError)
        self.assertEqual(str(context.exception), "provisionedProductId must be provided")

    def test_send_missing_instance_id(self: TestCase):
        # arrange
        mocked_event = {
            "operation": "PROVISION_PRODUCT",
            "tracerTag": {
                "key": "TRACER_TAG_DO_NOT_DELETE",
                "value": "pp-foo"
            },
            "provisionedProductId": "pp-id",
            "awsAccountId": "account-id",
            "provisionedProductName": "pp-name",
            "recordId": "rec-id",
            "launchRoleArn": "arn",
            "artifactPath": "artifact-path.tar.gz",
            "artifactType": "AWS_S3",
        }

        # act
        with self.assertRaises(RuntimeError) as context:
            send_apply_command.send(mocked_event, None)

        # assert
        self.assertEqual(context.expected, RuntimeError)
        self.assertEqual(str(context.exception), "instanceId must be provided")

    def test_send_missing_artifact_path(self: TestCase):
        # arrange
        mocked_event = {
            "instanceId": "instance-id",
            "operation": "PROVISION_PRODUCT",
            "tracerTag": {
                "key": "TRACER_TAG_DO_NOT_DELETE",
                "value": "pp-foo"
            },
            "provisionedProductId": "pp-id",
            "awsAccountId": "account-id",
            "provisionedProductName": "pp-name",
        }

        # act
        with self.assertRaises(RuntimeError) as context:
            send_apply_command.send(mocked_event, None)

        # assert
        self.assertEqual(context.expected, RuntimeError)
        self.assertEqual(str(context.exception), "artifactPath must be provided")

    def test_send_missing_artifact_type(self: TestCase):
        # arrange
        mocked_event = {
            "instanceId": "instance-id",
            "operation": "PROVISION_PRODUCT",
            "tracerTag": {
                "key": "TRACER_TAG_DO_NOT_DELETE",
                "value": "pp-foo"
            },
            "provisionedProductId": "pp-id",
            "awsAccountId": "account-id",
            "provisionedProductName": "pp-name",
            "artifactPath": "artifact.path.tar.gz"
        }

        # act
        with self.assertRaises(RuntimeError) as context:
            send_apply_command.send(mocked_event, None)

        # assert
        self.assertEqual(context.expected, RuntimeError)
        self.assertEqual(str(context.exception), "artifactType must be provided")

    def test_send_missing_launch_role(self: TestCase):
        # arrange
        mocked_event = {
            "instanceId": "instance-id",
            "operation": "PROVISION_PRODUCT",
            "tracerTag": {
                "key": "TRACER_TAG_DO_NOT_DELETE",
                "value": "pp-foo"
            },
            "provisionedProductId": "pp-id",
            "awsAccountId": "account-id",
            "provisionedProductName": "pp-name",
            "artifactPath": "artifact.path.tar.gz",
            "artifactType": "AWS_S3"
        }

        # act
        with self.assertRaises(RuntimeError) as context:
            send_apply_command.send(mocked_event, None)

        # assert
        self.assertEqual(context.expected, RuntimeError)
        self.assertEqual(str(context.exception), "launchRoleArn must be provided")

    def test_send_missing_aws_account_id(self: TestCase):
        # arrange
        mocked_event = {
            "instanceId": "instance-id",
            "operation": "PROVISION_PRODUCT",
            "provisionedProductId": "pp-id"
        }

        # act
        with self.assertRaises(RuntimeError) as context:
            send_apply_command.send(mocked_event, None)

        # assert
        self.assertEqual(context.expected, RuntimeError)
        self.assertEqual(str(context.exception), "awsAccountId must be provided")

if __name__ == '__main__':
    main()

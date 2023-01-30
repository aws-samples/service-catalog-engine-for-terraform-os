import io
import json
from unittest import main, TestCase
from unittest.mock import patch, MagicMock, Mock

from botocore.exceptions import ClientError

import get_state_file_outputs


class TestGetStateFileOutputs(TestCase):

    def __build_s3_response(self, state_file_contents: dict) -> dict:
        state_file_json_string = json.dumps(state_file_contents)
        encoded_state_file = str.encode(state_file_json_string)
        state_file_stream = io.BytesIO(encoded_state_file)
        return {
            "Body": state_file_stream
        }

    def setUp(self):
        # This is required to reset the mocks
        get_state_file_outputs.app_config = None
        get_state_file_outputs.s3_resource_client = None

    @patch('get_state_file_outputs.Configuration')
    @patch('get_state_file_outputs.os')
    @patch('boto3.resource')
    def test_get_state_file_outputs_happy_path(
        self: TestCase,
        mocked_client: MagicMock,
        mocked_os: MagicMock,
        mocked_configuration: MagicMock):

        # arrange
        event = {
            "provisionedProductId": "pp-id",
            "provisionedProductName": "pp-name",
            "awsAccountId": "account-id"
        }
        state_file_contents = {
            "version": 4,
            "terraform_version": "1.2.8",
            "serial": 0,
            "lineage": "10987ffd-dd9d-a446-72e0-da93f1016721",
            "outputs": {
                "test_output_key_1": {
                    "value": "test value 1",
                    "type": "string",
                    "description": "test description"
                },
                "test_output_key_2": {
                    "value": 3,
                    "type": "number",
                    "sensitive": False
                }
            }
        }
        expected_record_outputs = [
            {
                "key": "test_output_key_1",
                "value": "test value 1",
                "description": "test description"
            },
            {
                "key": "test_output_key_2",
                "value": "3",
                "description": None
            }
        ]

        s3_response = self.__build_s3_response(state_file_contents)
        state_bucket_name = 'state-bucket-name'
        mocked_os.environ.__getitem__.return_value = state_bucket_name
        mocked_app_config = Mock()
        mocked_app_config.get_region.return_value = 'us-east-1'
        mocked_configuration.return_value = mocked_app_config
        mocked_s3_resource_client: MagicMock = mocked_client.return_value
        mocked_s3_resource_client.Object.return_value.get.return_value = s3_response

        # act
        actual_response = get_state_file_outputs.parse(event, None)

        # assert
        mocked_configuration.assert_called_once()
        mocked_client.assert_called_once_with('s3', config=mocked_app_config.get_boto_config())
        mocked_s3_resource_client.Object.assert_called_once_with(state_bucket_name, "account-id/pp-id")
        mocked_s3_resource_client.Object.return_value.get.assert_called_once()
        self.assertEqual(actual_response, {'recordOutputs': expected_record_outputs})

    @patch('get_state_file_outputs.Configuration')
    @patch('get_state_file_outputs.os')
    @patch('boto3.resource')
    def test_get_state_file_outputs_with_sensitive_value(
        self: TestCase,
        mocked_client: MagicMock,
        mocked_os: MagicMock,
        mocked_configuration: MagicMock):

        # arrange
        event = {
            "provisionedProductId": "pp-id",
            "provisionedProductName": "pp-name",
            "awsAccountId": "account-id"
        }
        state_file_contents = {
            "version": 4,
            "terraform_version": "1.2.8",
            "serial": 0,
            "lineage": "10987ffd-dd9d-a446-72e0-da93f1016721",
            "outputs": {
                "test_output_key_1": {
                    "value": "test value 1",
                    "type": "string",
                    "description": "test description",
                    "sensitive": True
                },
            }
        }
        expected_record_outputs = [
            {
                "key": "test_output_key_1",
                "value": "(sensitive value)",
                "description": "test description"
            }
        ]

        s3_response = self.__build_s3_response(state_file_contents)

        state_bucket_name = 'state-bucket-name'
        mocked_os.environ.__getitem__.return_value = state_bucket_name
        mocked_app_config = Mock()
        mocked_app_config.get_region.return_value = 'us-east-1'
        mocked_configuration.return_value = mocked_app_config
        mocked_s3_resource_client: MagicMock = mocked_client.return_value
        mocked_s3_resource_client.Object.return_value.get.return_value = s3_response

        # act
        actual_response = get_state_file_outputs.parse(event, None)

        # assert
        mocked_configuration.assert_called_once()
        mocked_client.assert_called_once_with('s3', config=mocked_app_config.get_boto_config())
        mocked_s3_resource_client.Object.assert_called_once_with(state_bucket_name, "account-id/pp-id")
        mocked_s3_resource_client.Object.return_value.get.assert_called_once()
        self.assertEqual(actual_response, {'recordOutputs': expected_record_outputs})

    @patch('get_state_file_outputs.Configuration')
    @patch('get_state_file_outputs.os')
    @patch('boto3.resource')
    def test_get_state_file_outputs_with_empty_outputs_happy_path(
        self: TestCase,
        mocked_client: MagicMock,
        mocked_os: MagicMock,
        mocked_configuration: MagicMock):

        # arrange
        event = {
            "provisionedProductId": "pp-id",
            "provisionedProductName": "pp-name",
            "awsAccountId": "account-id",
        }
        state_file_contents = {
            "version": 4,
            "terraform_version": "1.2.8",
            "serial": 0,
            "lineage": "10987ffd-dd9d-a446-72e0-da93f1016721",
            "outputs": {}
        }
        expected_record_outputs = []

        s3_response = self.__build_s3_response(state_file_contents)
        state_bucket_name = 'state-bucket-name'
        mocked_os.environ.__getitem__.return_value = state_bucket_name
        mocked_app_config = Mock()
        mocked_app_config.get_region.return_value = 'us-east-1'
        mocked_configuration.return_value = mocked_app_config
        mocked_s3_resource_client: MagicMock = mocked_client.return_value
        mocked_s3_resource_client.Object.return_value.get.return_value = s3_response

        # act
        actual_response = get_state_file_outputs.parse(event, None)

        # assert
        mocked_configuration.assert_called_once()
        mocked_client.assert_called_once_with('s3', config=mocked_app_config.get_boto_config())
        mocked_s3_resource_client.Object.assert_called_once_with(state_bucket_name, "account-id/pp-id")
        mocked_s3_resource_client.Object.return_value.get.assert_called_once()
        self.assertEqual(actual_response, {'recordOutputs': expected_record_outputs})

    @patch('get_state_file_outputs.Configuration')
    @patch('get_state_file_outputs.os')
    @patch('boto3.resource')
    def test_get_state_file_outputs_with_no_outputs_happy_path(
        self: TestCase,
        mocked_client: MagicMock,
        mocked_os: MagicMock,
        mocked_configuration: MagicMock):

        # arrange
        event = {
            "provisionedProductId": "pp-id",
            "provisionedProductName": "pp-name",
            "awsAccountId": "account-id"
        }
        state_file_contents = {
            "version": 4,
            "terraform_version": "1.2.8",
            "serial": 0,
            "lineage": "10987ffd-dd9d-a446-72e0-da93f1016721"
        }
        expected_record_outputs = []

        s3_response = self.__build_s3_response(state_file_contents)
        state_bucket_name = 'state-bucket-name'
        mocked_os.environ.__getitem__.return_value = state_bucket_name
        mocked_app_config = Mock()
        mocked_app_config.get_region.return_value = 'us-east-1'
        mocked_configuration.return_value = mocked_app_config
        mocked_s3_resource_client: MagicMock = mocked_client.return_value
        mocked_s3_resource_client.Object.return_value.get.return_value = s3_response

        # act
        actual_response = get_state_file_outputs.parse(event, None)

        # assert
        mocked_configuration.assert_called_once()
        mocked_client.assert_called_once_with('s3', config=mocked_app_config.get_boto_config())
        mocked_s3_resource_client.Object.assert_called_once_with(state_bucket_name, "account-id/pp-id")
        mocked_s3_resource_client.Object.return_value.get.assert_called_once()
        self.assertEqual(actual_response, {'recordOutputs': expected_record_outputs})

    @patch('get_state_file_outputs.Configuration')
    @patch('get_state_file_outputs.os')
    @patch('boto3.resource')
    def test_get_state_file_outputs_with_s3_client_error(
        self: TestCase,
        mocked_client: MagicMock,
        mocked_os: MagicMock,
        mocked_configuration: MagicMock):

        # arrange
        event = {
            "provisionedProductId": "pp-id",
            "provisionedProductName": "pp-name",
            "awsAccountId": "account-id"
        }

        error_response = {
            'Error': {
                'Message': 'Some S3 4XX or 5XX error'
            },
            'ResponseMetadata': {
                'RequestId': 'some-random-uuid'
            }
        }

        state_bucket_name = 'state-bucket-name'
        mocked_os.environ.__getitem__.return_value = state_bucket_name
        mocked_app_config = Mock()
        mocked_app_config.get_region.return_value = 'us-east-1'
        mocked_configuration.return_value = mocked_app_config
        mocked_s3_resource_client: MagicMock = mocked_client.return_value
        mocked_s3_resource_client.Object.return_value.get.side_effect = ClientError(
            operation_name='get',
            error_response=error_response
        )

        # act
        with self.assertRaises(ClientError) as context:
            get_state_file_outputs.parse(event, None)

        # assert
        mocked_configuration.assert_called_once()
        mocked_client.assert_called_once_with('s3', config=mocked_app_config.get_boto_config())
        mocked_s3_resource_client.Object.assert_called_once_with(state_bucket_name, "account-id/pp-id")
        mocked_s3_resource_client.Object.return_value.get.assert_called_once()
        self.assertEqual(context.expected, ClientError)
        self.assertEqual(context.exception.response, error_response)

    @patch('get_state_file_outputs.Configuration')
    @patch('get_state_file_outputs.os')
    @patch('boto3.resource')
    def test_get_state_file_outputs_with_invalid_state_file(
        self: TestCase,
        mocked_client: MagicMock,
        mocked_os: MagicMock,
        mocked_configuration: MagicMock):

        # arrange
        event = {
            "provisionedProductId": "pp-id",
            "provisionedProductName": "pp-name",
            "awsAccountId": "account-id"
        }

        encoded_state_file = str.encode("invalid state file")
        state_file_stream = io.BytesIO(encoded_state_file)

        s3_response = {
            "Body": state_file_stream
        }

        state_bucket_name = 'state-bucket-name'
        mocked_os.environ.__getitem__.return_value = state_bucket_name
        mocked_app_config = Mock()
        mocked_app_config.get_region.return_value = 'us-east-1'
        mocked_configuration.return_value = mocked_app_config
        mocked_s3_resource_client: MagicMock = mocked_client.return_value
        mocked_s3_resource_client.Object.return_value.get.return_value = s3_response

        # act
        with self.assertRaises(RuntimeError) as context:
            get_state_file_outputs.parse(event, None)

        # assert
        mocked_configuration.assert_called_once()
        mocked_client.assert_called_once_with('s3', config=mocked_app_config.get_boto_config())
        mocked_s3_resource_client.Object.assert_called_once_with(state_bucket_name, "account-id/pp-id")
        mocked_s3_resource_client.Object.return_value.get.assert_called_once()
        self.assertEqual(context.expected, RuntimeError)
        self.assertEqual(str(context.exception), "File account-id/pp-id in bucket state-bucket-name is not in JSON format")

    @patch('get_state_file_outputs.Configuration')
    @patch('get_state_file_outputs.os')
    @patch('boto3.resource')
    def test_get_state_file_outputs_with_missing_output_value(
        self: TestCase,
        mocked_client: MagicMock,
        mocked_os: MagicMock,
        mocked_configuration: MagicMock):

        # arrange
        event = {
            "provisionedProductId": "pp-id",
            "provisionedProductName": "pp-name",
            "awsAccountId": "account-id"
        }
        state_file_contents = {
            "version": 4,
            "terraform_version": "1.2.8",
            "serial": 0,
            "lineage": "10987ffd-dd9d-a446-72e0-da93f1016721",
            "outputs": {
                "test_output_key": {
                    "type": "string"
                }
            }
        }

        s3_response = self.__build_s3_response(state_file_contents)
        state_bucket_name = 'state-bucket-name'
        mocked_os.environ.__getitem__.return_value = state_bucket_name
        mocked_app_config = Mock()
        mocked_app_config.get_region.return_value = 'us-east-1'
        mocked_configuration.return_value = mocked_app_config
        mocked_s3_resource_client: MagicMock = mocked_client.return_value
        mocked_s3_resource_client.Object.return_value.get.return_value = s3_response

        # act
        with self.assertRaises(RuntimeError) as context:
            get_state_file_outputs.parse(event, None)

        # assert
        mocked_configuration.assert_called_once()
        mocked_client.assert_called_once_with('s3', config=mocked_app_config.get_boto_config())
        mocked_s3_resource_client.Object.assert_called_once_with(state_bucket_name, "account-id/pp-id")
        mocked_s3_resource_client.Object.return_value.get.assert_called_once()
        self.assertEqual(context.expected, RuntimeError)
        self.assertEqual(str(context.exception), "Output value is missing for output test_output_key")

    @patch('get_state_file_outputs.Configuration')
    @patch('get_state_file_outputs.os')
    @patch('boto3.resource')
    def test_get_state_file_outputs_with_missing_provisioned_product_id_input(
        self: TestCase,
        mocked_client: MagicMock,
        mocked_os: MagicMock,
        mocked_configuration: MagicMock):

        # arrange
        event = {
            "provisionedProductName": "pp-name",
            "awsAccountId": "account-id"
        }

        state_bucket_name = 'state-bucket-name'
        mocked_os.environ.__getitem__.return_value = state_bucket_name
        mocked_app_config = Mock()
        mocked_app_config.get_region.return_value = 'us-east-1'
        mocked_configuration.return_value = mocked_app_config
        mocked_s3_resource_client: MagicMock = mocked_client.return_value

        # act
        with self.assertRaises(RuntimeError) as context:
            get_state_file_outputs.parse(event, None)

        # assert
        mocked_configuration.assert_not_called()
        mocked_client.assert_not_called()
        mocked_s3_resource_client.Object.assert_not_called()
        self.assertEqual(context.expected, RuntimeError)
        self.assertEqual(str(context.exception), "provisionedProductId must be provided")

    @patch('get_state_file_outputs.Configuration')
    @patch('get_state_file_outputs.os')
    @patch('boto3.resource')
    def test_get_state_file_outputs_with_missing_aws_account_id_input(
            self: TestCase,
            mocked_client: MagicMock,
            mocked_os: MagicMock,
            mocked_configuration: MagicMock):

        # arrange
        event = {
            "provisionedProductId": "pp-id",
            "provisionedProductName": "pp-name"
        }

        state_bucket_name = 'state-bucket-name'
        mocked_os.environ.__getitem__.return_value = state_bucket_name
        mocked_app_config = Mock()
        mocked_app_config.get_region.return_value = 'us-east-1'
        mocked_configuration.return_value = mocked_app_config
        mocked_s3_resource_client: MagicMock = mocked_client.return_value

        # act
        with self.assertRaises(RuntimeError) as context:
            get_state_file_outputs.parse(event, None)

        # assert
        mocked_configuration.assert_not_called()
        mocked_client.assert_not_called()
        mocked_s3_resource_client.Object.assert_not_called()
        self.assertEqual(context.expected, RuntimeError)
        self.assertEqual(str(context.exception), "awsAccountId must be provided")

if __name__ == '__main__':
    main()

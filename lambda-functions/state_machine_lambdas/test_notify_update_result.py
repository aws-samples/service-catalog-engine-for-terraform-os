from unittest import main, TestCase
from unittest.mock import MagicMock, Mock, patch, ANY

from botocore.exceptions import ClientError

import notify_update_result


class LambdaContext:
    def __init__(self, invoked_function_arn: str):
        self.invoked_function_arn = invoked_function_arn


class TestNotifyUpdateProvisionedProductEngineWorkflowResult(TestCase):

    def setUp(self: TestCase):
        # This is required to reset the mocks
        notify_update_result.app_config = None
        notify_update_result.service_catalog_facade = None

    @patch('notify_update_result.Configuration')
    @patch('notify_update_result.service_catalog_facade')
    def test_notify_succeeded_happy_path(self: TestCase,
                                         mocked_service_catalog_facade: MagicMock,
                                         mocked_configuration: MagicMock):

        # arrange
        mocked_app_config = Mock()
        mocked_app_config.get_region.return_value = 'us-east-1'
        mocked_configuration.return_value = mocked_app_config

        mocked_event = {
            "token": "token3000",
            "awsAccountId": "012345678910",
            "provisionedProductId": "pp-id",
            "provisionedProductName": "pp-name",
            "recordId": "rec-123",
            "outputs": [
                {
                    "key": "key1",
                    "value": "value1",
                    "description": "desc1"
                },
                {
                    "key": "key2",
                    "value": "value2"
                },
                {
                    "key": "key3",
                    "value": "value3",
                    "description": None
                }
            ]
        }

        lambda_context: LambdaContext = LambdaContext(
            'arn:aws:lambda:us-east-1:264796065659:function:NotifyUpdateProvisionedProductEngineWorkflowResult')

        expected_service_catalog_outputs =[
            {
                "OutputKey": "key1",
                "OutputValue": "value1",
                "Description": "desc1"
            },
            {
                "OutputKey": "key2",
                "OutputValue": "value2"
            },
            {
                "OutputKey": "key3",
                "OutputValue": "value3"
            }
        ]

        # act
        notify_update_result.notify(mocked_event, lambda_context)

        # assert
        mocked_configuration.assert_called_once()
        mocked_service_catalog_facade.notify_update_succeeded.assert_called_once_with(
            workflow_token = mocked_event['token'],
            record_id = mocked_event['recordId'],
            outputs = expected_service_catalog_outputs
        )

    @patch('notify_update_result.Configuration')
    @patch('notify_update_result.service_catalog_facade')
    def test_notify_with_tre_failure(self: TestCase,
                                     mocked_service_catalog_facade: MagicMock,
                                     mocked_configuration: MagicMock):
        # arrange
        mocked_app_config = Mock()
        mocked_app_config.get_region.return_value = 'us-east-1'
        mocked_configuration.return_value = mocked_app_config

        mocked_event = {
            "token": "token3000",
            "awsAccountId": "012345678910",
            "provisionedProductId": "pp-id",
            "provisionedProductName": "pp-name",
            "recordId": "rec-123",
            "error": "RuntimeError",
            "errorMessage": "I failed",
            "outputs": [
                {
                    "key": "key1",
                    "value": "value1",
                    "description": "desc1"
                }
            ]
        }

        expected_service_catalog_outputs = [
            {
                'OutputKey': 'key1',
                'OutputValue': 'value1',
                'Description': 'desc1'
            }
        ]

        lambda_context: LambdaContext = LambdaContext(
            'arn:aws:lambda:us-east-1:264796065659:function:NotifyUpdateProvisionedProductEngineWorkflowResult')

        # act
        notify_update_result.notify(mocked_event, lambda_context)

        # assert
        mocked_configuration.assert_called_once()
        mocked_service_catalog_facade.notify_update_failed.assert_called_once_with(
            workflow_token = mocked_event['token'],
            record_id = mocked_event['recordId'],
            failure_reason = mocked_event['errorMessage'],
            outputs = expected_service_catalog_outputs
        )

    @patch('notify_update_result.Configuration')
    @patch('notify_update_result.service_catalog_facade')
    def test_notify_when_succeeded_internal_error(self: TestCase,
                                                  mocked_service_catalog_facade: MagicMock,
                                                  mocked_configuration: MagicMock):
        # arrange
        mocked_app_config = Mock()
        mocked_app_config.get_region.return_value = 'us-east-1'
        mocked_configuration.return_value = mocked_app_config

        mocked_event = {
            "token": "token3000",
            "awsAccountId": "012345678910",
            "provisionedProductId": "pp-id",
            "provisionedProductName": "pp-name",
            "recordId": "rec-123",
            "outputs": [
                {
                    "key": "key1",
                    "value": "value1",
                    "description": "desc1"
                }
            ]
        }
        expected_service_catalog_outputs =[
            {
                "OutputKey": "key1",
                "OutputValue": "value1",
                "Description": "desc1"
            }
        ]

        lambda_context: LambdaContext = LambdaContext(
            'arn:aws:lambda:us-east-1:264796065659:function:NotifyUpdateProvisionedProductEngineWorkflowResult')

        error_response = {
            'Error': {
                'Message': 'An internal error has occurred'
            },
            'ResponseMetadata': {
                'RequestId': 'some-random-uuid'
            }
        }
        mocked_client_error = ClientError(
            operation_name='NotifyUpdateProvisionedProductEngineWorkflowResult',
            error_response=error_response
        )
        mocked_service_catalog_facade.notify_update_succeeded.side_effect = mocked_client_error

        # act
        with self.assertRaises(ClientError) as context:
            notify_update_result.notify(mocked_event, lambda_context)

        # assert
        mocked_configuration.assert_called_once()
        mocked_service_catalog_facade.notify_update_succeeded.assert_called_once_with(
            workflow_token = mocked_event['token'],
            record_id = mocked_event['recordId'],
            outputs = expected_service_catalog_outputs
        )

        self.assertEqual(context.expected, ClientError)
        self.assertEqual(context.exception, mocked_client_error)

    @patch('notify_update_result.Configuration')
    @patch('notify_update_result.service_catalog_facade')
    def test_notify_when_failed_internal_error(self: TestCase,
                                               mocked_service_catalog_facade: MagicMock,
                                               mocked_configuration: MagicMock):
        # arrange
        mocked_app_config = Mock()
        mocked_app_config.get_region.return_value = 'us-east-1'
        mocked_configuration.return_value = mocked_app_config

        mocked_event = {
            "token": "token3000",
            "awsAccountId": "012345678910",
            "provisionedProductId": "pp-id",
            "provisionedProductName": "pp-name",
            "recordId": "rec-123",
            "error": "RuntimeError",
            "errorMessage": "I failed",
            "outputs": []
        }

        lambda_context: LambdaContext = LambdaContext(
            'arn:aws:lambda:us-east-1:264796065659:function:NotifyUpdateProvisionedProductEngineWorkflowResult')

        error_response = {
            'Error': {
                'Message': 'An internal error has occurred'
            },
            'ResponseMetadata': {
                'RequestId': 'some-random-uuid'
            }
        }
        mocked_client_error = ClientError(
            operation_name='NotifyUpdateProvisionedProductEngineWorkflowResult',
            error_response=error_response
        )
        mocked_service_catalog_facade.notify_update_failed.side_effect = mocked_client_error

        # act
        with self.assertRaises(ClientError) as context:
            notify_update_result.notify(mocked_event, lambda_context)

        # assert
        mocked_configuration.assert_called_once()
        mocked_service_catalog_facade.notify_update_failed.assert_called_once_with(
            workflow_token = mocked_event['token'],
            record_id = mocked_event['recordId'],
            failure_reason = mocked_event['errorMessage'],
            outputs = []
        )

        self.assertEqual(context.expected, ClientError)
        self.assertEqual(context.exception, mocked_client_error)


if __name__ == '__main__':
    main()

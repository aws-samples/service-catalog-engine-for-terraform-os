from unittest import main, TestCase
from unittest.mock import MagicMock, Mock, patch, ANY

from botocore.exceptions import ClientError

import notify_terminate_result


class LambdaContext:
    def __init__(self, invoked_function_arn: str):
        self.invoked_function_arn = invoked_function_arn


class TestNotifyTerminateResult(TestCase):

    def setUp(self: TestCase):
        # This is required to reset the mocks
        notify_terminate_result.app_config = None
        notify_terminate_result.service_catalog_facade = None

    @patch('notify_terminate_result.Configuration')
    @patch('notify_terminate_result.service_catalog_facade')
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
            "recordId": "rec-123"
        }

        lambda_context: LambdaContext = LambdaContext(
            'arn:aws:lambda:us-east-1:264796065659:function:NotifyProvisionProductEngineWorkflowResult')

        # act
        notify_terminate_result.notify(mocked_event, lambda_context)

        # assert
        mocked_configuration.assert_called_once()
        mocked_service_catalog_facade.notify_terminate_succeeded.assert_called_once_with(
            workflow_token = mocked_event['token'],
            record_id = mocked_event['recordId'],
        )

    @patch('notify_terminate_result.Configuration')
    @patch('notify_terminate_result.service_catalog_facade')
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
            "errorMessage": "I failed"
        }

        lambda_context: LambdaContext = LambdaContext(
            'arn:aws:lambda:us-east-1:264796065659:function:NotifyProvisionProductEngineWorkflowResult')

        # act
        notify_terminate_result.notify(mocked_event, lambda_context)

        # assert
        mocked_configuration.assert_called_once()
        mocked_service_catalog_facade.notify_terminate_failed.assert_called_once_with(
            workflow_token = mocked_event['token'],
            record_id = mocked_event['recordId'],
            failure_reason = mocked_event['errorMessage']
        )

    @patch('notify_terminate_result.Configuration')
    @patch('notify_terminate_result.service_catalog_facade')
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
            "recordId": "rec-123"
        }

        lambda_context: LambdaContext = LambdaContext(
            'arn:aws:lambda:us-east-1:264796065659:function:NotifyProvisionProductEngineWorkflowResult')

        error_response = {
            'Error': {
                'Message': 'An internal error has occurred'
            },
            'ResponseMetadata': {
                'RequestId': 'some-random-uuid'
            }
        }
        mocked_client_error = ClientError(
            operation_name='NotifyProvisionProductEngineWorkflowResult',
            error_response=error_response
        )
        mocked_service_catalog_facade.notify_terminate_succeeded.side_effect = mocked_client_error

        # act
        with self.assertRaises(ClientError) as context:
            notify_terminate_result.notify(mocked_event, lambda_context)

        # assert
        mocked_configuration.assert_called_once()
        mocked_service_catalog_facade.notify_terminate_succeeded.assert_called_once_with(
            workflow_token = mocked_event['token'],
            record_id = mocked_event['recordId']
        )

        self.assertEqual(context.expected, ClientError)
        self.assertEqual(context.exception, mocked_client_error)

    @patch('notify_terminate_result.Configuration')
    @patch('notify_terminate_result.service_catalog_facade')
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
            "errorMessage": "I failed"
        }

        lambda_context: LambdaContext = LambdaContext(
            'arn:aws:lambda:us-east-1:264796065659:function:NotifyProvisionProductEngineWorkflowResult')

        error_response = {
            'Error': {
                'Message': 'An internal error has occurred'
            },
            'ResponseMetadata': {
                'RequestId': 'some-random-uuid'
            }
        }
        mocked_client_error = ClientError(
            operation_name='NotifyProvisionProductEngineWorkflowResult',
            error_response=error_response
        )
        mocked_service_catalog_facade.notify_terminate_failed.side_effect = mocked_client_error

        # act
        with self.assertRaises(ClientError) as context:
            notify_terminate_result.notify(mocked_event, lambda_context)

        # assert
        mocked_configuration.assert_called_once()
        mocked_service_catalog_facade.notify_terminate_failed.assert_called_once_with(
            workflow_token = mocked_event['token'],
            record_id = mocked_event['recordId'],
            failure_reason = mocked_event['errorMessage']
        )

        self.assertEqual(context.expected, ClientError)
        self.assertEqual(context.exception, mocked_client_error)


if __name__ == '__main__':
    main()

import os
from unittest import main, TestCase
from unittest.mock import MagicMock, Mock, patch, ANY

import boto3
from botocore.exceptions import ClientError

from core.service_catalog_facade import ServiceCatalogFacade

class TestServiceCatalogFacade(TestCase):

    @patch('boto3.client')
    @patch.dict(os.environ, {
        'AWS_REGION': 'us-west-2',
        'SERVICE_CATALOG_VERIFY_SSL': 'true',
        'SERVICE_CATALOG_ENDPOINT': ''
    })
    def test_notify_provision_succeeded_happy_path(self: TestCase,
        mocked_boto3_client: MagicMock):

        # Arrange
        mocked_app_config = Mock()
        mocked_boto_config = Mock()
        mocked_app_config.get_boto_config.return_value = mocked_boto_config

        mocked_service_catalog_client = Mock()
        mocked_boto3_client.return_value = mocked_service_catalog_client
        mocked_client_response = {'ResponseMetadata': {'RequestId': 'request-id'}}
        mocked_service_catalog_client.notify_provision_product_engine_workflow_result.return_value = mocked_client_response

        service_catalog_facade = ServiceCatalogFacade(mocked_app_config)

        workflow_token = 'token'
        record_id = "record"
        tracer_tag_key = 'tracer_key'
        tracer_tag_value = 'tracer_value'
        outputs = [{'OutputKey': 'output-key', 'OutputValue': 'output-value'}]

        # Act
        service_catalog_facade.notify_provision_succeeded(
            workflow_token = workflow_token,
            record_id = record_id,
            tracer_tag_key = tracer_tag_key,
            tracer_tag_value = tracer_tag_value,
            outputs = outputs
            )

        # Assert
        mocked_boto3_client.assert_called_once_with('servicecatalog',
            verify = True,
            config = mocked_app_config.get_boto_config())

        mocked_service_catalog_client.notify_provision_product_engine_workflow_result.assert_called_once_with(
            WorkflowToken = workflow_token,
            RecordId = record_id,
            Status = 'SUCCEEDED',
            ResourceIdentifier = {
                'UniqueTag': {
                    'Key': tracer_tag_key,
                    'Value': tracer_tag_value
                }
            },
            Outputs =     outputs,
            IdempotencyToken=ANY
        )

    @patch('boto3.client')
    @patch.dict(os.environ, {
        'AWS_REGION': 'us-west-2',
        'SERVICE_CATALOG_VERIFY_SSL': 'false',
        'SERVICE_CATALOG_ENDPOINT': 'endpoint-override'
    })
    def test_notify_provision_succeeded_using_service_catalog_overrides(self: TestCase,
        mocked_boto3_client: MagicMock):

        # Arrange
        mocked_app_config = Mock()
        mocked_boto_config = Mock()
        mocked_app_config.get_boto_config.return_value = mocked_boto_config

        mocked_service_catalog_client = Mock()
        mocked_boto3_client.return_value = mocked_service_catalog_client
        mocked_client_response = {'ResponseMetadata': {'RequestId': 'request-id'}}
        mocked_service_catalog_client.notify_provision_product_engine_workflow_result.return_value = mocked_client_response

        service_catalog_facade = ServiceCatalogFacade(mocked_app_config)

        workflow_token = 'token'
        record_id = "record"
        tracer_tag_key = 'tracer_key'
        tracer_tag_value = 'tracer_value'
        outputs = [{'OutputKey': 'output-key', 'OutputValue': 'output-value'}]

        # Act
        service_catalog_facade.notify_provision_succeeded(
            workflow_token = workflow_token,
            record_id = record_id,
            tracer_tag_key = tracer_tag_key,
            tracer_tag_value = tracer_tag_value,
            outputs = outputs
            )

        # Assert
        mocked_boto3_client.assert_called_once_with('servicecatalog',
            verify = False,
            endpoint_url = 'endpoint-override',
            config = mocked_app_config.get_boto_config())

        mocked_service_catalog_client.notify_provision_product_engine_workflow_result.assert_called_once_with(
            WorkflowToken = workflow_token,
            RecordId = record_id,
            Status = 'SUCCEEDED',
            ResourceIdentifier = {
                'UniqueTag': {
                    'Key': tracer_tag_key,
                    'Value': tracer_tag_value
                }
            },
            Outputs =     outputs,
            IdempotencyToken=ANY
        )

    @patch('boto3.client')
    @patch.dict(os.environ, {
        'AWS_REGION': 'us-west-2',
        'SERVICE_CATALOG_VERIFY_SSL': 'true',
        'SERVICE_CATALOG_ENDPOINT': ''
    })
    def test_notify_provision_succeeded_raises_client_error(self: TestCase,
        mocked_boto3_client: MagicMock):

        # Arrange
        mocked_app_config = Mock()
        mocked_boto_config = Mock()
        mocked_app_config.get_boto_config.return_value = mocked_boto_config

        mocked_service_catalog_client = Mock()
        mocked_boto3_client.return_value = mocked_service_catalog_client

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
        mocked_service_catalog_client.notify_provision_product_engine_workflow_result.side_effect = mocked_client_error

        service_catalog_facade = ServiceCatalogFacade(mocked_app_config)

        workflow_token = 'token'
        record_id = "record"
        tracer_tag_key = 'tracer_key'
        tracer_tag_value = 'tracer_value'
        outputs = [{'OutputKey': 'output-key', 'OutputValue': 'output-value'}]

        # Act
        with self.assertRaises(ClientError) as context:
            service_catalog_facade.notify_provision_succeeded(
                workflow_token = workflow_token,
                record_id = record_id,
                tracer_tag_key = tracer_tag_key,
                tracer_tag_value = tracer_tag_value,
                outputs = outputs
            )

        # Assert
        mocked_boto3_client.assert_called_once_with('servicecatalog',
            verify = True,
            config = mocked_app_config.get_boto_config())

        mocked_service_catalog_client.notify_provision_product_engine_workflow_result.assert_called_once_with(
            WorkflowToken = workflow_token,
            RecordId = record_id,
            Status = 'SUCCEEDED',
            ResourceIdentifier = {
                'UniqueTag': {
                    'Key': tracer_tag_key,
                    'Value': tracer_tag_value
                }
            },
            Outputs = outputs,
            IdempotencyToken=ANY
        )
        self.assertEqual(context.expected, ClientError)
        self.assertEqual(context.exception, mocked_client_error)

    @patch('boto3.client')
    @patch.dict(os.environ, {
        'AWS_REGION': 'us-west-2',
        'SERVICE_CATALOG_VERIFY_SSL': 'true',
        'SERVICE_CATALOG_ENDPOINT': ''
    })
    def test_notify_provision_failed_happy_path(self: TestCase,
        mocked_boto3_client: MagicMock):

        # Arrange
        mocked_app_config = Mock()
        mocked_boto_config = Mock()
        mocked_app_config.get_boto_config.return_value = mocked_boto_config

        mocked_service_catalog_client = Mock()
        mocked_boto3_client.return_value = mocked_service_catalog_client
        mocked_client_response = {'ResponseMetadata': {'RequestId': 'request-id'}}
        mocked_service_catalog_client.notify_provision_product_engine_workflow_result.return_value = mocked_client_response

        service_catalog_facade = ServiceCatalogFacade(mocked_app_config)

        workflow_token = 'token'
        record_id = "record"
        failure_reason = 'something went wrong'
        tracer_tag_key = 'tracer_key'
        tracer_tag_value = 'tracer_value'
        outputs = [{'OutputKey': 'output-key', 'OutputValue': 'output-value'}]

        # Act
        service_catalog_facade.notify_provision_failed(
            workflow_token = workflow_token,
            record_id = record_id,
            failure_reason = failure_reason,
            tracer_tag_key = tracer_tag_key,
            tracer_tag_value = tracer_tag_value,
            outputs = outputs
            )

        # Assert
        mocked_boto3_client.assert_called_once_with('servicecatalog',
            verify = True,
            config = mocked_app_config.get_boto_config())

        mocked_service_catalog_client.notify_provision_product_engine_workflow_result.assert_called_once_with(
            WorkflowToken = workflow_token,
            RecordId = record_id,
            Status = 'FAILED',
            FailureReason = failure_reason,
            ResourceIdentifier = {
                'UniqueTag': {
                    'Key': tracer_tag_key,
                    'Value': tracer_tag_value
                }
            },
            Outputs =     outputs,
            IdempotencyToken=ANY
        )

    @patch('boto3.client')
    @patch.dict(os.environ, {
        'AWS_REGION': 'us-west-2',
        'SERVICE_CATALOG_VERIFY_SSL': 'true',
        'SERVICE_CATALOG_ENDPOINT': ''
    })
    def test_notify_provision_failed_raises_client_error(self: TestCase,
        mocked_boto3_client: MagicMock):

        # Arrange
        mocked_app_config = Mock()
        mocked_boto_config = Mock()
        mocked_app_config.get_boto_config.return_value = mocked_boto_config

        mocked_service_catalog_client = Mock()
        mocked_boto3_client.return_value = mocked_service_catalog_client

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
        mocked_service_catalog_client.notify_provision_product_engine_workflow_result.side_effect = mocked_client_error

        service_catalog_facade = ServiceCatalogFacade(mocked_app_config)

        workflow_token = 'token'
        record_id = "record"
        failure_reason = 'failure reason'
        tracer_tag_key = 'tracer_key'
        tracer_tag_value = 'tracer_value'
        outputs = [{'OutputKey': 'output-key', 'OutputValue': 'output-value'}]

        # Act
        with self.assertRaises(ClientError) as context:
            service_catalog_facade.notify_provision_failed(
                workflow_token = workflow_token,
                record_id = record_id,
                failure_reason = failure_reason,
                tracer_tag_key = tracer_tag_key,
                tracer_tag_value = tracer_tag_value,
                outputs = outputs
            )

        # Assert
        mocked_boto3_client.assert_called_once_with('servicecatalog',
            verify = True,
            config = mocked_app_config.get_boto_config())

        mocked_service_catalog_client.notify_provision_product_engine_workflow_result.assert_called_once_with(
            WorkflowToken = workflow_token,
            RecordId = record_id,
            Status = 'FAILED',
            FailureReason = failure_reason,
            ResourceIdentifier = {
                'UniqueTag': {
                    'Key': tracer_tag_key,
                    'Value': tracer_tag_value
                }
            },
            Outputs = outputs,
            IdempotencyToken=ANY
        )
        self.assertEqual(context.expected, ClientError)
        self.assertEqual(context.exception, mocked_client_error)

    @patch('boto3.client')
    @patch.dict(os.environ, {
        'AWS_REGION': 'us-west-2',
        'SERVICE_CATALOG_VERIFY_SSL': 'true',
        'SERVICE_CATALOG_ENDPOINT': ''
    })
    def test_notify_update_succeeded_happy_path(self: TestCase,
                                                mocked_boto3_client: MagicMock):

        # Arrange
        mocked_app_config = Mock()
        mocked_boto_config = Mock()
        mocked_app_config.get_boto_config.return_value = mocked_boto_config

        mocked_service_catalog_client = Mock()
        mocked_boto3_client.return_value = mocked_service_catalog_client
        mocked_client_response = {'ResponseMetadata': {'RequestId': 'request-id'}}
        mocked_service_catalog_client.notify_update_provisioned_product_engine_workflow_result.return_value = mocked_client_response

        service_catalog_facade = ServiceCatalogFacade(mocked_app_config)

        workflow_token = 'token'
        record_id = "record"
        outputs = [{'OutputKey': 'output-key', 'OutputValue': 'output-value'}]

        # Act
        service_catalog_facade.notify_update_succeeded(
            workflow_token = workflow_token,
            record_id = record_id,
            outputs = outputs
        )

        # Assert
        mocked_boto3_client.assert_called_once_with('servicecatalog',
            verify = True,
                                                    config = mocked_app_config.get_boto_config())

        mocked_service_catalog_client.notify_update_provisioned_product_engine_workflow_result.assert_called_once_with(
            WorkflowToken = workflow_token,
            RecordId = record_id,
            Status = 'SUCCEEDED',
            Outputs = outputs,
            IdempotencyToken=ANY
        )

    @patch('boto3.client')
    @patch.dict(os.environ, {
        'AWS_REGION': 'us-west-2',
        'SERVICE_CATALOG_VERIFY_SSL': 'true',
        'SERVICE_CATALOG_ENDPOINT': ''
    })
    def test_notify_update_succeeded_raises_client_error(self: TestCase,
                                                            mocked_boto3_client: MagicMock):

        # Arrange
        mocked_app_config = Mock()
        mocked_boto_config = Mock()
        mocked_app_config.get_boto_config.return_value = mocked_boto_config

        mocked_service_catalog_client = Mock()
        mocked_boto3_client.return_value = mocked_service_catalog_client

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
        mocked_service_catalog_client.notify_update_provisioned_product_engine_workflow_result.side_effect = mocked_client_error

        service_catalog_facade = ServiceCatalogFacade(mocked_app_config)

        workflow_token = 'token'
        record_id = "record"
        outputs = [{'OutputKey': 'output-key', 'OutputValue': 'output-value'}]

        # Act
        with self.assertRaises(ClientError) as context:
            service_catalog_facade.notify_update_succeeded(
                workflow_token = workflow_token,
                record_id = record_id,
                outputs = outputs
            )

        # Assert
        mocked_boto3_client.assert_called_once_with('servicecatalog',
            verify = True,
                                                    config = mocked_app_config.get_boto_config())

        mocked_service_catalog_client.notify_update_provisioned_product_engine_workflow_result.assert_called_once_with(
            WorkflowToken = workflow_token,
            RecordId = record_id,
            Status = 'SUCCEEDED',
            Outputs = outputs,
            IdempotencyToken=ANY
        )
        self.assertEqual(context.expected, ClientError)
        self.assertEqual(context.exception, mocked_client_error)

    @patch('boto3.client')
    @patch.dict(os.environ, {
        'AWS_REGION': 'us-west-2',
        'SERVICE_CATALOG_VERIFY_SSL': 'true',
        'SERVICE_CATALOG_ENDPOINT': ''
    })
    def test_notify_update_failed_happy_path(self: TestCase,
                                                mocked_boto3_client: MagicMock):

        # Arrange
        mocked_app_config = Mock()
        mocked_boto_config = Mock()
        mocked_app_config.get_boto_config.return_value = mocked_boto_config

        mocked_service_catalog_client = Mock()
        mocked_boto3_client.return_value = mocked_service_catalog_client
        mocked_client_response = {'ResponseMetadata': {'RequestId': 'request-id'}}
        mocked_service_catalog_client.notify_update_provisioned_product_engine_workflow_result.return_value = mocked_client_response

        service_catalog_facade = ServiceCatalogFacade(mocked_app_config)

        workflow_token = 'token'
        record_id = "record"
        failure_reason = 'something went wrong'
        outputs = [{'OutputKey': 'output-key', 'OutputValue': 'output-value'}]

        # Act
        service_catalog_facade.notify_update_failed(
            workflow_token = workflow_token,
            record_id = record_id,
            failure_reason = failure_reason,
            outputs = outputs
        )

        # Assert
        mocked_boto3_client.assert_called_once_with('servicecatalog',
            verify = True,
                                                    config = mocked_app_config.get_boto_config())

        mocked_service_catalog_client.notify_update_provisioned_product_engine_workflow_result.assert_called_once_with(
            WorkflowToken = workflow_token,
            RecordId = record_id,
            Status = 'FAILED',
            FailureReason = failure_reason,
            Outputs = outputs,
            IdempotencyToken=ANY
        )

    @patch('boto3.client')
    @patch.dict(os.environ, {
        'AWS_REGION': 'us-west-2',
        'SERVICE_CATALOG_VERIFY_SSL': 'true',
        'SERVICE_CATALOG_ENDPOINT': ''
    })
    def test_notify_update_failed_raises_client_error(self: TestCase,
                                                         mocked_boto3_client: MagicMock):

        # Arrange
        mocked_app_config = Mock()
        mocked_boto_config = Mock()
        mocked_app_config.get_boto_config.return_value = mocked_boto_config

        mocked_service_catalog_client = Mock()
        mocked_boto3_client.return_value = mocked_service_catalog_client

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
        mocked_service_catalog_client.notify_update_provisioned_product_engine_workflow_result.side_effect = mocked_client_error

        service_catalog_facade = ServiceCatalogFacade(mocked_app_config)

        workflow_token = 'token'
        record_id = "record"
        failure_reason = 'failure reason'
        outputs = [{'OutputKey': 'output-key', 'OutputValue': 'output-value'}]

        # Act
        with self.assertRaises(ClientError) as context:
            service_catalog_facade.notify_update_failed(
                workflow_token = workflow_token,
                record_id = record_id,
                failure_reason = failure_reason,
                outputs = outputs
            )

        # Assert
        mocked_boto3_client.assert_called_once_with('servicecatalog',
            verify = True,
                                                    config = mocked_app_config.get_boto_config())

        mocked_service_catalog_client.notify_update_provisioned_product_engine_workflow_result.assert_called_once_with(
            WorkflowToken = workflow_token,
            RecordId = record_id,
            Status = 'FAILED',
            FailureReason = failure_reason,
            Outputs = outputs,
            IdempotencyToken=ANY
        )
        self.assertEqual(context.expected, ClientError)
        self.assertEqual(context.exception, mocked_client_error)

    @patch('boto3.client')
    @patch.dict(os.environ, {
        'AWS_REGION': 'us-west-2',
        'SERVICE_CATALOG_VERIFY_SSL': 'true',
        'SERVICE_CATALOG_ENDPOINT': ''
    })
    def test_notify_terminate_succeeded_happy_path(self: TestCase,
        mocked_boto3_client: MagicMock):

        # Arrange
        mocked_app_config = Mock()
        mocked_boto_config = Mock()
        mocked_app_config.get_boto_config.return_value = mocked_boto_config

        mocked_service_catalog_client = Mock()
        mocked_boto3_client.return_value = mocked_service_catalog_client
        mocked_client_response = {'ResponseMetadata': {'RequestId': 'request-id'}}
        mocked_service_catalog_client.notify_terminate_provisioned_product_engine_workflow_result.return_value = mocked_client_response

        service_catalog_facade = ServiceCatalogFacade(mocked_app_config)

        workflow_token = 'token'
        record_id = "record"

        # Act
        service_catalog_facade.notify_terminate_succeeded(
            workflow_token = workflow_token,
            record_id = record_id,
            )

        # Assert
        mocked_boto3_client.assert_called_once_with('servicecatalog',
            verify = True,
            config = mocked_app_config.get_boto_config())

        mocked_service_catalog_client.notify_terminate_provisioned_product_engine_workflow_result.assert_called_once_with(
            WorkflowToken = workflow_token,
            RecordId = record_id,
            Status = 'SUCCEEDED',
            IdempotencyToken=ANY
        )

    @patch('boto3.client')
    @patch.dict(os.environ, {
        'AWS_REGION': 'us-west-2',
        'SERVICE_CATALOG_VERIFY_SSL': 'true',
        'SERVICE_CATALOG_ENDPOINT': ''
    })
    def test_notify_terminate_succeeded_raises_client_error(self: TestCase,
        mocked_boto3_client: MagicMock):

        # Arrange
        mocked_app_config = Mock()
        mocked_boto_config = Mock()
        mocked_app_config.get_boto_config.return_value = mocked_boto_config

        mocked_service_catalog_client = Mock()
        mocked_boto3_client.return_value = mocked_service_catalog_client

        error_response = {
            'Error': {
                'Message': 'An internal error has occurred'
            },
            'ResponseMetadata': {
                'RequestId': 'some-random-uuid'
            }
        }
        mocked_client_error = ClientError(
            operation_name='NotifyTerminateProvisionedProductEngineWorkflowResult',
            error_response=error_response
        )
        mocked_service_catalog_client.notify_terminate_provisioned_product_engine_workflow_result.side_effect = mocked_client_error

        service_catalog_facade = ServiceCatalogFacade(mocked_app_config)

        workflow_token = 'token'
        record_id = "record"

        # Act
        with self.assertRaises(ClientError) as context:
            service_catalog_facade.notify_terminate_succeeded(
                workflow_token = workflow_token,
                record_id = record_id,
            )

        # Assert
        mocked_boto3_client.assert_called_once_with('servicecatalog',
            verify = True,
            config = mocked_app_config.get_boto_config())

        mocked_service_catalog_client.notify_terminate_provisioned_product_engine_workflow_result.assert_called_once_with(
            WorkflowToken = workflow_token,
            RecordId = record_id,
            Status = 'SUCCEEDED',
            IdempotencyToken=ANY
        )
        self.assertEqual(context.expected, ClientError)
        self.assertEqual(context.exception, mocked_client_error)

    @patch('boto3.client')
    @patch.dict(os.environ, {
        'AWS_REGION': 'us-west-2',
        'SERVICE_CATALOG_VERIFY_SSL': 'true',
        'SERVICE_CATALOG_ENDPOINT': ''
    })
    def test_notify_terminate_failed_happy_path(self: TestCase,
        mocked_boto3_client: MagicMock):

        # Arrange
        mocked_app_config = Mock()
        mocked_boto_config = Mock()
        mocked_app_config.get_boto_config.return_value = mocked_boto_config

        mocked_service_catalog_client = Mock()
        mocked_boto3_client.return_value = mocked_service_catalog_client
        mocked_client_response = {'ResponseMetadata': {'RequestId': 'request-id'}}
        mocked_service_catalog_client.notify_terminate_provisioned_product_engine_workflow_result.return_value = mocked_client_response

        service_catalog_facade = ServiceCatalogFacade(mocked_app_config)

        workflow_token = 'token'
        record_id = "record"
        failure_reason = 'something went wrong'

        # Act
        service_catalog_facade.notify_terminate_failed(
            workflow_token = workflow_token,
            record_id = record_id,
            failure_reason = failure_reason
            )

        # Assert
        mocked_boto3_client.assert_called_once_with('servicecatalog',
            verify = True,
            config = mocked_app_config.get_boto_config())

        mocked_service_catalog_client.notify_terminate_provisioned_product_engine_workflow_result.assert_called_once_with(
            WorkflowToken = workflow_token,
            RecordId = record_id,
            Status = 'FAILED',
            FailureReason = failure_reason,
            IdempotencyToken=ANY
        )

    @patch('boto3.client')
    @patch.dict(os.environ, {
        'AWS_REGION': 'us-west-2',
        'SERVICE_CATALOG_VERIFY_SSL': 'true',
        'SERVICE_CATALOG_ENDPOINT': ''
    })
    def test_notify_terminate_failed_raises_client_error(self: TestCase,
        mocked_boto3_client: MagicMock):

        # Arrange
        mocked_app_config = Mock()
        mocked_boto_config = Mock()
        mocked_app_config.get_boto_config.return_value = mocked_boto_config

        mocked_service_catalog_client = Mock()
        mocked_boto3_client.return_value = mocked_service_catalog_client

        error_response = {
            'Error': {
                'Message': 'An internal error has occurred'
            },
            'ResponseMetadata': {
                'RequestId': 'some-random-uuid'
            }
        }
        mocked_client_error = ClientError(
            operation_name='NotifyTerminateProvisionedProductEngineWorkflowResult',
            error_response=error_response
        )
        mocked_service_catalog_client.notify_terminate_provisioned_product_engine_workflow_result.side_effect = mocked_client_error

        service_catalog_facade = ServiceCatalogFacade(mocked_app_config)

        workflow_token = 'token'
        record_id = "record"
        failure_reason = 'failure reason'

        # Act
        with self.assertRaises(ClientError) as context:
            service_catalog_facade.notify_terminate_failed(
                workflow_token = workflow_token,
                record_id = record_id,
                failure_reason = failure_reason
            )

        # Assert
        mocked_boto3_client.assert_called_once_with('servicecatalog',
            verify = True,
            config = mocked_app_config.get_boto_config())

        mocked_service_catalog_client.notify_terminate_provisioned_product_engine_workflow_result.assert_called_once_with(
            WorkflowToken = workflow_token,
            RecordId = record_id,
            Status = 'FAILED',
            FailureReason = failure_reason,
            IdempotencyToken=ANY
        )
        self.assertEqual(context.expected, ClientError)
        self.assertEqual(context.exception, mocked_client_error)


if __name__ == '__main__':
    main()

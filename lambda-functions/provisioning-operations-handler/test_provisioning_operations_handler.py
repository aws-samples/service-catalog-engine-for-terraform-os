from unittest import main, TestCase
from unittest.mock import patch, MagicMock, ANY
from botocore.exceptions import ClientError
import provisioning_operations_handler


def get_os_environ_side_effect(value):
    if value == 'AWS_REGION':
        return 'us-east-1'
    elif value == 'STATE_MACHINE_ARN':
        return 'SM_ARN'
    raise KeyError(value)


class TestProvisioningOperationsHandler(TestCase):

    def setUp(self):
        # This is required to reset the mocks
        provisioning_operations_handler.step_functions_client = None

    @patch('provisioning_operations_handler.os')
    @patch('boto3.client')
    def test_handle_sqs_records_given_one_record(self: TestCase,
                                                 mocked_client: MagicMock,
                                                 mocked_os: MagicMock):
        # Arrange
        mocked_event = {
            "Records": [
                {
                    "messageId": "d9d3e061-8811-4663-89d6-3745e2d2d42f",
                    "receiptHandle": "AQEBZBicFXj0lCq8aV53EqtVF+1w0tBT8ndecHb14MisdvNhuIbyAl1mycSLWiwBRMygNl2oqNxy+6fZb3vfn/9Tc/uSFdop26kGqhpvP5nY+oNKL/x19YtE1lrGifu7ud/8+RTGhSKOeWVjLCYWwn5uKrFnD6DpZRtVJNDHao3/giVUeggMv7w7ETU9qC056nVg9BPshemagqODXHd99B+AE/fBcsln0c6Z7unwEK0oWZ2SSL9IhTChhnEursrtXpdOAiTzZuVJLchVOR4YW0Nvt3PRMWpcfPw6Mo0yWNSnXdPBPamhFShofh068VL+iW8zbfVa4BnI+Rs4DRIiuFFDEnqTMwWvSsyn30jvttg8kFS+Sx40Qw2yh5lNS6C5WM2KHU6pH89qRCUYoxOKZ9QIBtD98uRxYbdwMoAN6byUUbM=",
                    "body": "{\"token\": \"tok-foo\", \"operation\": \"PROVISION_PRODUCT\", \"provisionedProductId\": \"pp-foo\", \"provisionedProductName\": \"TerraformSimpleS3Bucket\", \"productId\": \"prod-foo\", \"provisioningArtifactId\": \"pa-foo\", \"recordId\": \"rec-foo9\", \"launchRoleArn\": \"arn:aws:iam::264796065659:role/SCLaunchRoleTerraformExample\", \"artifact\": {\"path\": \"s3zx://tfez-test-terraform-templates/s3.tar.gz\", \"type\": \"AWS_S3\"}, \"identity\": {\"principal\": \"\", \"awsAccountId\": \"264796065659\", \"organizationId\": \"\"}, \"parameters\": [{\"key\": \"bucket_name\", \"value\": \"test-tf-engine\"}]}",
                    "attributes": {
                        "ApproximateReceiveCount": "1",
                        "SentTimestamp": "1669761558610",
                        "SenderId": "AROAT3JYTJ55UE74NI4T7:dummy-sender",
                        "ApproximateFirstReceiveTimestamp": "1669761558615"
                    },
                    "messageAttributes": {},
                    "md5OfBody": "da1b86a1aa3e13bceac7d57b1cea34c2",
                    "eventSource": "aws:sqs",
                    "eventSourceARN": "arn:aws:sqs:us-east-1:264796065659:TerraformEngineProvisioningQueue",
                    "awsRegion": "us-east-1"
                }
            ]
        }

        mocked_os.environ.get.side_effect = get_os_environ_side_effect
        mocked_sfn_client = mocked_client.return_value
        mocked_sfn_client.start_execution.return_value = {
            'executionArn': 'some-execution-arn',
            'ResponseMetadata': {
                'RequestId': 'random-requestId'
            }
        }

        # Act
        result = provisioning_operations_handler.handle_sqs_records(mocked_event, None)

        # Assert
        mocked_client.assert_called_once_with('stepfunctions', config=ANY)
        self.assertEqual(mocked_os.environ.get.call_args_list[0].args[0], 'AWS_REGION')
        self.assertEqual(mocked_os.environ.get.call_args_list[1].args[0], 'STATE_MACHINE_ARN')
        mocked_sfn_client.start_execution.assert_called_once_with(
            stateMachineArn='SM_ARN',
            name='pp-foo-rec-foo9',
            input=mocked_event['Records'][0]['body']
        )
        self.assertEqual(result, {"batchItemFailures": []})


    @patch('provisioning_operations_handler.os')
    @patch('boto3.client')
    def test_handle_sqs_records_given_two_records(self: TestCase,
                                                  mocked_client: MagicMock,
                                                  mocked_os: MagicMock):
        # Arrange
        mocked_event = {
            "Records": [
                {
                    "messageId": "d9d3e061-8811-4663-89d6-3745e2d2d42f",
                    "receiptHandle": "AQEBZBicFXj0lCq8aV53EqtVF+1w0tBT8ndecHb14MisdvNhuIbyAl1mycSLWiwBRMygNl2oqNxy+6fZb3vfn/9Tc/uSFdop26kGqhpvP5nY+oNKL/x19YtE1lrGifu7ud/8+RTGhSKOeWVjLCYWwn5uKrFnD6DpZRtVJNDHao3/giVUeggMv7w7ETU9qC056nVg9BPshemagqODXHd99B+AE/fBcsln0c6Z7unwEK0oWZ2SSL9IhTChhnEursrtXpdOAiTzZuVJLchVOR4YW0Nvt3PRMWpcfPw6Mo0yWNSnXdPBPamhFShofh068VL+iW8zbfVa4BnI+Rs4DRIiuFFDEnqTMwWvSsyn30jvttg8kFS+Sx40Qw2yh5lNS6C5WM2KHU6pH89qRCUYoxOKZ9QIBtD98uRxYbdwMoAN6byUUbM=",
                    "body": "{\"token\": \"tok-foo\", \"operation\": \"PROVISION_PRODUCT\", \"provisionedProductId\": \"pp-foo\", \"provisionedProductName\": \"TerraformSimpleS3Bucket\", \"productId\": \"prod-foo\", \"provisioningArtifactId\": \"pa-foo\", \"recordId\": \"rec-foo9\", \"launchRoleArn\": \"arn:aws:iam::264796065659:role/SCLaunchRoleTerraformExample\", \"artifact\": {\"path\": \"s3://tfe-test-terraform-templates/s3.tar.gz\", \"type\": \"AWS_S3\"}, \"identity\": {\"principal\": \"\", \"awsAccountId\": \"264796065659\", \"organizationId\": \"\"}, \"parameters\": [{\"key\": \"bucket_name\", \"value\": \"test-tf-engine\"}]}",
                    "attributes": {
                        "ApproximateReceiveCount": "1",
                        "SentTimestamp": "1669761558610",
                        "SenderId": "AROAT3JYTJ55UE74NI4T7:dummy-sender",
                        "ApproximateFirstReceiveTimestamp": "1669761558615"
                    },
                    "messageAttributes": {},
                    "md5OfBody": "da1b86a1aa3e13bceac7d57b1cea34c2",
                    "eventSource": "aws:sqs",
                    "eventSourceARN": "arn:aws:sqs:us-east-1:264796065659:TerraformEngineProvisioningQueue",
                    "awsRegion": "us-east-1"
                },
                {
                    "messageId": "d9d3e061-8811-4663-89d6-3745e2d2dg6g",
                    "receiptHandle": "AQEBZBicFXj0lCq8aV53EqtVF+1w0tBT8ndecHb14MisdvNhuIbyAl1mycSLWiwBRMygNl2oqNxy+6fZb3vfn/9Tc/uSFdop26kGqhpvP5nY+oNKL/x19YtE1lrGifu7ud/8+RTGhSKOeWVjLCYWwn5uKrFnD6DpZRtVJNDHao3/giVUeggMv7w7ETU9qC056nVg9BPshemagqODXHd99B+AE/fBcsln0c6Z7unwEK0oWZ2SSL9IhTChhnEursrtXpdOAiTzZuVJLchVOR4YW0Nvt3PRMWpcfPw6Mo0yWNSnXdPBPamhFShofh068VL+iW8zbfVa4BnI+Rs4DRIiuFFDEnqTMwWvSsyn30jvttg8kFS+Sx40Qw2yh5lNS6C5WM2KHU6pH89qRCUYoxOKZ9QIBtD98uRxYbdwMoAN6byUUbM=",
                    "body": "{\"token\": \"tok-foo\", \"operation\": \"PROVISION_PRODUCT\", \"provisionedProductId\": \"pp-foo1\", \"provisionedProductName\": \"TerraformSimpleS3Bucket\", \"productId\": \"prod-foo\", \"provisioningArtifactId\": \"pa-foo\", \"recordId\": \"rec-foo2\", \"launchRoleArn\": \"arn:aws:iam::264796065659:role/SCLaunchRoleTerraformExample\", \"artifact\": {\"path\": \"s3://tfe-test-terraform-templates/s3.tar.gz\", \"type\": \"AWS_S3\"}, \"identity\": {\"principal\": \"\", \"awsAccountId\": \"264796065659\", \"organizationId\": \"\"}, \"parameters\": [{\"key\": \"bucket_name\", \"value\": \"test-tf-engine\"}]}",
                    "attributes": {
                        "ApproximateReceiveCount": "1",
                        "SentTimestamp": "1669761558610",
                        "SenderId": "AROAT3JYTJ55UE74NI4T7:dummy-sender",
                        "ApproximateFirstReceiveTimestamp": "1669761558615"
                    },
                    "messageAttributes": {},
                    "md5OfBody": "da1b86a1aa3e13bceac7d57b1cea34c2",
                    "eventSource": "aws:sqs",
                    "eventSourceARN": "arn:aws:sqs:us-east-1:264796065659:TerraformEngineProvisioningQueue",
                    "awsRegion": "us-east-1"
                }
            ]
        }

        mocked_os.environ.get.side_effect = get_os_environ_side_effect
        mocked_sfn_client = mocked_client.return_value
        mocked_sfn_client.start_execution.side_effect = [
            {
                'executionArn': 'some-execution-arn1',
                'ResponseMetadata': {
                    'RequestId': 'random-requestId1'
                }
            },
            {
                'executionArn': 'some-execution-arn2',
                'ResponseMetadata': {
                    'RequestId': 'random-requestId2'
                }
            }
        ]

        # Act
        result = provisioning_operations_handler.handle_sqs_records(mocked_event, None)

        # Assert
        mocked_client.assert_called_once_with('stepfunctions', config=ANY)
        self.assertEqual(mocked_os.environ.get.call_args_list[0].args[0], 'AWS_REGION')
        self.assertEqual(mocked_os.environ.get.call_args_list[1].args[0], 'STATE_MACHINE_ARN')

        first_invocation = mocked_sfn_client.start_execution.call_args_list[0]
        self.assertEqual(first_invocation.kwargs['stateMachineArn'], 'SM_ARN')
        self.assertEqual(first_invocation.kwargs['name'], 'pp-foo-rec-foo9')
        self.assertEqual(first_invocation.kwargs['input'], mocked_event['Records'][0]['body'])

        second_invocation = mocked_sfn_client.start_execution.call_args_list[1]
        self.assertEqual(second_invocation.kwargs['stateMachineArn'], 'SM_ARN')
        self.assertEqual(second_invocation.kwargs['name'], 'pp-foo1-rec-foo2')
        self.assertEqual(second_invocation.kwargs['input'], mocked_event['Records'][1]['body'])

        self.assertEqual(result, {"batchItemFailures": []})

    @patch('provisioning_operations_handler.os')
    @patch('boto3.client')
    def test_handle_sqs_records_given_execution_already_exists_exception(self: TestCase,
                                                                         mocked_client: MagicMock,
                                                                         mocked_os: MagicMock):
        # Arrange
        mocked_event = {
            "Records": [
                {
                    "messageId": "d9d3e061-8811-4663-89d6-3745e2d2d42f",
                    "receiptHandle": "AQEBZBicFXj0lCq8aV53EqtVF+1w0tBT8ndecHb14MisdvNhuIbyAl1mycSLWiwBRMygNl2oqNxy+6fZb3vfn/9Tc/uSFdop26kGqhpvP5nY+oNKL/x19YtE1lrGifu7ud/8+RTGhSKOeWVjLCYWwn5uKrFnD6DpZRtVJNDHao3/giVUeggMv7w7ETU9qC056nVg9BPshemagqODXHd99B+AE/fBcsln0c6Z7unwEK0oWZ2SSL9IhTChhnEursrtXpdOAiTzZuVJLchVOR4YW0Nvt3PRMWpcfPw6Mo0yWNSnXdPBPamhFShofh068VL+iW8zbfVa4BnI+Rs4DRIiuFFDEnqTMwWvSsyn30jvttg8kFS+Sx40Qw2yh5lNS6C5WM2KHU6pH89qRCUYoxOKZ9QIBtD98uRxYbdwMoAN6byUUbM=",
                    "body": "{\"token\": \"tok-foo\", \"operation\": \"PROVISION_PRODUCT\", \"provisionedProductId\": \"pp-foo\", \"provisionedProductName\": \"TerraformSimpleS3Bucket\", \"productId\": \"prod-foo\", \"provisioningArtifactId\": \"pa-foo\", \"recordId\": \"rec-foo9\", \"artifact\": {\"path\": \"s3://tfe-test-terraform-templates/s3.tar.gz\", \"tpye\": \"AWS_S3\"}, \"callerIdentity\": {\"principal\": \"\", \"awsAccountId\": \"264796065659\", \"organizationId\": \"\"}, \"launchRoleArn\": \"arn:aws:iam::264796065659:role/SCLaunchRoleTerraformExample\", \"parameters\": [{\"key\": \"bucket_name\", \"value\": \"test-tf-engine\"}]}",
                    "attributes": {
                        "ApproximateReceiveCount": "1",
                        "SentTimestamp": "1669761558610",
                        "SenderId": "AROAT3JYTJ55UE74NI4T7:dummy-sender",
                        "ApproximateFirstReceiveTimestamp": "1669761558615"
                    },
                    "messageAttributes": {},
                    "md5OfBody": "da1b86a1aa3e13bceac7d57b1cea34c2",
                    "eventSource": "aws:sqs",
                    "eventSourceARN": "arn:aws:sqs:us-east-1:264796065659:TerraformEngineProvisioningQueue",
                    "awsRegion": "us-east-1"
                }
            ]
        }

        error_response = {
            'Error': {
                'Message': 'Some State machine 4XX or 5XX error',
                'Code': 'ExecutionAlreadyExists'
            },
            'ResponseMetadata': {
                'RequestId': 'some-random-uuid'
            }
        }

        mocked_os.environ.get.side_effect = get_os_environ_side_effect
        mocked_sfn_client = mocked_client.return_value
        mocked_sfn_client.start_execution.side_effect = ClientError(
            operation_name='start_execution',
            error_response=error_response
        )

        # Act
        result = provisioning_operations_handler.handle_sqs_records(mocked_event, None)

        # Assert
        mocked_client.assert_called_once_with('stepfunctions', config=ANY)
        self.assertEqual(mocked_os.environ.get.call_args_list[0].args[0], 'AWS_REGION')
        self.assertEqual(mocked_os.environ.get.call_args_list[1].args[0], 'STATE_MACHINE_ARN')
        mocked_sfn_client.start_execution.assert_called_once_with(
            stateMachineArn='SM_ARN',
            name='pp-foo-rec-foo9',
            input=mocked_event['Records'][0]['body']
        )
        self.assertEqual(result, {"batchItemFailures": []})

    @patch('provisioning_operations_handler.os')
    @patch('boto3.client')
    def test_handle_sqs_records_given_sfn_unhandled_exception(self: TestCase,
                                                              mocked_client: MagicMock,
                                                              mocked_os: MagicMock):
        # Arrange
        mocked_event = {
            "Records": [
                {
                    "messageId": "d9d3e061-8811-4663-89d6-3745e2d2d42f",
                    "receiptHandle": "AQEBZBicFXj0lCq8aV53EqtVF+1w0tBT8ndecHb14MisdvNhuIbyAl1mycSLWiwBRMygNl2oqNxy+6fZb3vfn/9Tc/uSFdop26kGqhpvP5nY+oNKL/x19YtE1lrGifu7ud/8+RTGhSKOeWVjLCYWwn5uKrFnD6DpZRtVJNDHao3/giVUeggMv7w7ETU9qC056nVg9BPshemagqODXHd99B+AE/fBcsln0c6Z7unwEK0oWZ2SSL9IhTChhnEursrtXpdOAiTzZuVJLchVOR4YW0Nvt3PRMWpcfPw6Mo0yWNSnXdPBPamhFShofh068VL+iW8zbfVa4BnI+Rs4DRIiuFFDEnqTMwWvSsyn30jvttg8kFS+Sx40Qw2yh5lNS6C5WM2KHU6pH89qRCUYoxOKZ9QIBtD98uRxYbdwMoAN6byUUbM=",
                    "body": "{\"token\": \"tok-foo\", \"operation\": \"PROVISION_PRODUCT\", \"provisionedProductId\": \"pp-foo\", \"provisionedProductName\": \"TerraformSimpleS3Bucket\", \"productId\": \"prod-foo\", \"provisioningArtifactId\": \"pa-foo\", \"recordId\": \"rec-foo9\", \"artifact\": {\"path\": \"s3://tfe-test-terraform-templates/s3.tar.gz\", \"type\": \"AWS_S3\"}, \"callerIdentity\": {\"principal\": \"\", \"awsAccountId\": \"264796065659\", \"organizationId\": \"\"}, \"launchRoleArn\": \"arn:aws:iam::264796065659:role/SCLaunchRoleTerraformExample\", \"parameters\": [{\"key\": \"bucket_name\", \"value\": \"test-tf-engine\"}]}",
                    "attributes": {
                        "ApproximateReceiveCount": "1",
                        "SentTimestamp": "1669761558610",
                        "SenderId": "AROAT3JYTJ55UE74NI4T7:dummy-sender",
                        "ApproximateFirstReceiveTimestamp": "1669761558615"
                    },
                    "messageAttributes": {},
                    "md5OfBody": "da1b86a1aa3e13bceac7d57b1cea34c2",
                    "eventSource": "aws:sqs",
                    "eventSourceARN": "arn:aws:sqs:us-east-1:264796065659:TerraformEngineProvisioningQueue",
                    "awsRegion": "us-east-1"
                }
            ]
        }

        error_response = {
            'Error': {
                'Message': 'Some State machine 4XX or 5XX error',
                'Code': 'SomeStepFunctionsError'
            },
            'ResponseMetadata': {
                'RequestId': 'some-random-uuid'
            }
        }

        mocked_os.environ.get.side_effect = get_os_environ_side_effect
        mocked_sfn_client = mocked_client.return_value
        mocked_sfn_client.start_execution.side_effect = ClientError(
            operation_name='start_execution',
            error_response=error_response
        )

        # Act
        result = provisioning_operations_handler.handle_sqs_records(mocked_event, None)

        # Assert
        mocked_client.assert_called_once_with('stepfunctions', config=ANY)
        self.assertEqual(mocked_os.environ.get.call_args_list[0].args[0], 'AWS_REGION')
        self.assertEqual(mocked_os.environ.get.call_args_list[1].args[0], 'STATE_MACHINE_ARN')
        mocked_sfn_client.start_execution.assert_called_once_with(
            stateMachineArn='SM_ARN',
            name='pp-foo-rec-foo9',
            input=mocked_event['Records'][0]['body']
        )
        self.assertEqual(result, { 
            "batchItemFailures": [
                {
                    "itemIdentifier": "d9d3e061-8811-4663-89d6-3745e2d2d42f"
                }
            ]
        })


    @patch('provisioning_operations_handler.os')
    @patch('boto3.client')
    def test_handle_sqs_records_given_generic_unhandled_exception(self: TestCase,
                                                              mocked_client: MagicMock,
                                                              mocked_os: MagicMock):
        # Arrange
        mocked_event = {
            "Records": [
                {
                    "messageId": "d9d3e061-8811-4663-89d6-3745e2d2d42f",
                    "receiptHandle": "AQEBZBicFXj0lCq8aV53EqtVF+1w0tBT8ndecHb14MisdvNhuIbyAl1mycSLWiwBRMygNl2oqNxy+6fZb3vfn/9Tc/uSFdop26kGqhpvP5nY+oNKL/x19YtE1lrGifu7ud/8+RTGhSKOeWVjLCYWwn5uKrFnD6DpZRtVJNDHao3/giVUeggMv7w7ETU9qC056nVg9BPshemagqODXHd99B+AE/fBcsln0c6Z7unwEK0oWZ2SSL9IhTChhnEursrtXpdOAiTzZuVJLchVOR4YW0Nvt3PRMWpcfPw6Mo0yWNSnXdPBPamhFShofh068VL+iW8zbfVa4BnI+Rs4DRIiuFFDEnqTMwWvSsyn30jvttg8kFS+Sx40Qw2yh5lNS6C5WM2KHU6pH89qRCUYoxOKZ9QIBtD98uRxYbdwMoAN6byUUbM=",
                    "body": "{\"token\": \"tok-foo\", \"operation\": \"PROVISION_PRODUCT\", \"provisionedProductName\": \"TerraformSimpleS3Bucket\", \"productId\": \"prod-foo\", \"provisioningArtifactId\": \"pa-foo\", \"recordId\": \"rec-foo9\", \"artifact\": {\"path\": \"s3://tfe-test-terraform-templates/s3.tar.gz\", \"type\": \"AWS_S3\"}, \"callerIdentity\": {\"principal\": \"\", \"awsAccountId\": \"264796065659\", \"organizationId\": \"\"}, \"launchRoleArn\": \"arn:aws:iam::264796065659:role/SCLaunchRoleTerraformExample\", \"tags\": [{\"key\": \"MessageType\", \"value\": \"ManualTest\"}], \"parameters\": [{\"key\": \"bucket_name\", \"value\": \"test-tf-engine\"}]}",
                    "attributes": {
                        "ApproximateReceiveCount": "1",
                        "SentTimestamp": "1669761558610",
                        "SenderId": "AROAT3JYTJ55UE74NI4T7:dummy-sender",
                        "ApproximateFirstReceiveTimestamp": "1669761558615"
                    },
                    "messageAttributes": {},
                    "md5OfBody": "da1b86a1aa3e13bceac7d57b1cea34c2",
                    "eventSource": "aws:sqs",
                    "eventSourceARN": "arn:aws:sqs:us-east-1:264796065659:TerraformEngineProvisioningQueue",
                    "awsRegion": "us-east-1"
                }
            ]
        }

        mocked_os.environ.get.side_effect = get_os_environ_side_effect
        mocked_sfn_client = mocked_client.return_value

        # Act
        result = provisioning_operations_handler.handle_sqs_records(mocked_event, None)

        # Assert
        mocked_client.assert_called_once_with('stepfunctions', config=ANY)
        self.assertEqual(mocked_os.environ.get.call_args_list[0].args[0], 'AWS_REGION')
        self.assertEqual(mocked_os.environ.get.call_args_list[1].args[0], 'STATE_MACHINE_ARN')
        self.assertEqual(result, { 
            "batchItemFailures": [
                {
                    "itemIdentifier": "d9d3e061-8811-4663-89d6-3745e2d2d42f"
                }
            ]
        })

    @patch('provisioning_operations_handler.os')
    @patch('boto3.client')
    def test_handle_sqs_records_given_missing_token(self: TestCase,
                                                              mocked_client: MagicMock,
                                                              mocked_os: MagicMock):
        # Arrange
        mocked_event = {
            "Records": [
                {
                    "messageId": "d9d3e061-8811-4663-89d6-3745e2d2d42f",
                    "receiptHandle": "AQEBZBicFXj0lCq8aV53EqtVF+1w0tBT8ndecHb14MisdvNhuIbyAl1mycSLWiwBRMygNl2oqNxy+6fZb3vfn/9Tc/uSFdop26kGqhpvP5nY+oNKL/x19YtE1lrGifu7ud/8+RTGhSKOeWVjLCYWwn5uKrFnD6DpZRtVJNDHao3/giVUeggMv7w7ETU9qC056nVg9BPshemagqODXHd99B+AE/fBcsln0c6Z7unwEK0oWZ2SSL9IhTChhnEursrtXpdOAiTzZuVJLchVOR4YW0Nvt3PRMWpcfPw6Mo0yWNSnXdPBPamhFShofh068VL+iW8zbfVa4BnI+Rs4DRIiuFFDEnqTMwWvSsyn30jvttg8kFS+Sx40Qw2yh5lNS6C5WM2KHU6pH89qRCUYoxOKZ9QIBtD98uRxYbdwMoAN6byUUbM=",
                    "body": "{\"operation\": \"PROVISION_PRODUCT\", \"provisionedProductName\": \"TerraformSimpleS3Bucket\", \"productId\": \"prod-foo\", \"provisioningArtifactId\": \"pa-foo\", \"recordId\": \"rec-foo9\", \"artifact\": {\"path\": \"s3://tfe-test-terraform-templates/s3.tar.gz\", \"type\": \"AWS_S3\"}, \"callerIdentity\": {\"principal\": \"\", \"awsAccountId\": \"264796065659\", \"organizationId\": \"\"}, \"launchRoleArn\": \"arn:aws:iam::264796065659:role/SCLaunchRoleTerraformExample\", \"tags\": [{\"key\": \"MessageType\", \"value\": \"ManualTest\"}], \"parameters\": [{\"key\": \"bucket_name\", \"value\": \"test-tf-engine\"}]}",
                    "attributes": {
                        "ApproximateReceiveCount": "1",
                        "SentTimestamp": "1669761558610",
                        "SenderId": "AROAT3JYTJ55UE74NI4T7:dummy-sender",
                        "ApproximateFirstReceiveTimestamp": "1669761558615"
                    },
                    "messageAttributes": {},
                    "md5OfBody": "da1b86a1aa3e13bceac7d57b1cea34c2",
                    "eventSource": "aws:sqs",
                    "eventSourceARN": "arn:aws:sqs:us-east-1:264796065659:TerraformEngineProvisioningQueue",
                    "awsRegion": "us-east-1"
                }
            ]
        }

        mocked_os.environ.get.side_effect = get_os_environ_side_effect
        mocked_sfn_client = mocked_client.return_value

        # Act
        result = provisioning_operations_handler.handle_sqs_records(mocked_event, None)

        # Assert
        mocked_client.assert_called_once_with('stepfunctions', config=ANY)
        self.assertEqual(mocked_os.environ.get.call_args_list[0].args[0], 'AWS_REGION')
        self.assertEqual(mocked_os.environ.get.call_args_list[1].args[0], 'STATE_MACHINE_ARN')
        self.assertEqual(result, { 
            "batchItemFailures": [
                {
                    "itemIdentifier": "d9d3e061-8811-4663-89d6-3745e2d2d42f"
                }
            ]
        })

    @patch('provisioning_operations_handler.os')
    @patch('boto3.client')
    def test_handle_sqs_records_given_two_records_and_one_fails(self: TestCase,
                                                  mocked_client: MagicMock,
                                                  mocked_os: MagicMock):
        # Arrange
        # The first message is invalid because it is missing record ID.
        # The second message is valid and will start the sfn execution successfully.
        mocked_event = {
            "Records": [
                {
                    "messageId": "d9d3e061-8811-4663-89d6-3745e2d2d42f",
                    "receiptHandle": "AQEBZBicFXj0lCq8aV53EqtVF+1w0tBT8ndecHb14MisdvNhuIbyAl1mycSLWiwBRMygNl2oqNxy+6fZb3vfn/9Tc/uSFdop26kGqhpvP5nY+oNKL/x19YtE1lrGifu7ud/8+RTGhSKOeWVjLCYWwn5uKrFnD6DpZRtVJNDHao3/giVUeggMv7w7ETU9qC056nVg9BPshemagqODXHd99B+AE/fBcsln0c6Z7unwEK0oWZ2SSL9IhTChhnEursrtXpdOAiTzZuVJLchVOR4YW0Nvt3PRMWpcfPw6Mo0yWNSnXdPBPamhFShofh068VL+iW8zbfVa4BnI+Rs4DRIiuFFDEnqTMwWvSsyn30jvttg8kFS+Sx40Qw2yh5lNS6C5WM2KHU6pH89qRCUYoxOKZ9QIBtD98uRxYbdwMoAN6byUUbM=",
                    "body": "{\"token\": \"tok-foo\", \"operation\": \"PROVISION_PRODUCT\", \"provisionedProductId\": \"pp-foo\", \"provisionedProductName\": \"TerraformSimpleS3Bucket\", \"productId\": \"prod-foo\", \"provisioningArtifactId\": \"pa-foo\", \"launchRoleArn\": \"arn:aws:iam::264796065659:role/SCLaunchRoleTerraformExample\", \"artifact\": {\"path\": \"s3://tfe-test-terraform-templates/s3.tar.gz\", \"type\": \"AWS_S3\"}, \"identity\": {\"principal\": \"\", \"awsAccountId\": \"264796065659\", \"organizationId\": \"\"}, \"parameters\": [{\"key\": \"bucket_name\", \"value\": \"test-tf-engine\"}]}",
                    "attributes": {
                        "ApproximateReceiveCount": "1",
                        "SentTimestamp": "1669761558610",
                        "SenderId": "AROAT3JYTJ55UE74NI4T7:dummy-sender",
                        "ApproximateFirstReceiveTimestamp": "1669761558615"
                    },
                    "messageAttributes": {},
                    "md5OfBody": "da1b86a1aa3e13bceac7d57b1cea34c2",
                    "eventSource": "aws:sqs",
                    "eventSourceARN": "arn:aws:sqs:us-east-1:264796065659:TerraformEngineProvisioningQueue",
                    "awsRegion": "us-east-1"
                },
                {
                    "messageId": "d9d3e061-8811-4663-89d6-3745e2d2dg6g",
                    "receiptHandle": "AQEBZBicFXj0lCq8aV53EqtVF+1w0tBT8ndecHb14MisdvNhuIbyAl1mycSLWiwBRMygNl2oqNxy+6fZb3vfn/9Tc/uSFdop26kGqhpvP5nY+oNKL/x19YtE1lrGifu7ud/8+RTGhSKOeWVjLCYWwn5uKrFnD6DpZRtVJNDHao3/giVUeggMv7w7ETU9qC056nVg9BPshemagqODXHd99B+AE/fBcsln0c6Z7unwEK0oWZ2SSL9IhTChhnEursrtXpdOAiTzZuVJLchVOR4YW0Nvt3PRMWpcfPw6Mo0yWNSnXdPBPamhFShofh068VL+iW8zbfVa4BnI+Rs4DRIiuFFDEnqTMwWvSsyn30jvttg8kFS+Sx40Qw2yh5lNS6C5WM2KHU6pH89qRCUYoxOKZ9QIBtD98uRxYbdwMoAN6byUUbM=",
                    "body": "{\"token\": \"tok-foo\", \"operation\": \"PROVISION_PRODUCT\", \"provisionedProductId\": \"pp-foo1\", \"provisionedProductName\": \"TerraformSimpleS3Bucket\", \"productId\": \"prod-foo\", \"provisioningArtifactId\": \"pa-foo\", \"recordId\": \"rec-foo2\", \"launchRoleArn\": \"arn:aws:iam::264796065659:role/SCLaunchRoleTerraformExample\", \"artifact\": {\"path\": \"s3://tfe-test-terraform-templates/s3.tar.gz\", \"type\": \"AWS_S3\"}, \"identity\": {\"principal\": \"\", \"awsAccountId\": \"264796065659\", \"organizationId\": \"\"}, \"parameters\": [{\"key\": \"bucket_name\", \"value\": \"test-tf-engine\"}]}",
                    "attributes": {
                        "ApproximateReceiveCount": "1",
                        "SentTimestamp": "1669761558610",
                        "SenderId": "AROAT3JYTJ55UE74NI4T7:dummy-sender",
                        "ApproximateFirstReceiveTimestamp": "1669761558615"
                    },
                    "messageAttributes": {},
                    "md5OfBody": "da1b86a1aa3e13bceac7d57b1cea34c2",
                    "eventSource": "aws:sqs",
                    "eventSourceARN": "arn:aws:sqs:us-east-1:264796065659:TerraformEngineProvisioningQueue",
                    "awsRegion": "us-east-1"
                }
            ]
        }

        mocked_os.environ.get.side_effect = get_os_environ_side_effect
        mocked_sfn_client = mocked_client.return_value
        mocked_sfn_client.start_execution.side_effect = [
            {
                'executionArn': 'some-execution-arn1',
                'ResponseMetadata': {
                    'RequestId': 'random-requestId1'
                }
            }
        ]

        # Act
        result = provisioning_operations_handler.handle_sqs_records(mocked_event, None)

        # Assert
        mocked_client.assert_called_once_with('stepfunctions', config=ANY)
        self.assertEqual(mocked_os.environ.get.call_args_list[0].args[0], 'AWS_REGION')
        self.assertEqual(mocked_os.environ.get.call_args_list[1].args[0], 'STATE_MACHINE_ARN')
        mocked_sfn_client.start_execution.assert_called_once_with(
            stateMachineArn='SM_ARN',
            name='pp-foo1-rec-foo2',
            input=mocked_event['Records'][1]['body']
        )
        self.assertEqual(result, { 
            "batchItemFailures": [
                {
                    "itemIdentifier": "d9d3e061-8811-4663-89d6-3745e2d2d42f"
                }
            ]
        })


if __name__ == '__main__':
    main()

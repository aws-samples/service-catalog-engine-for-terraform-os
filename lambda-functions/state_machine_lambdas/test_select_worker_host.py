from unittest import main, TestCase
from unittest.mock import patch, MagicMock

from botocore.exceptions import ClientError

import select_worker_host


class TestSelectWorkerHost(TestCase):

    def setUp(self):
        # This is required to reset the mocks
        select_worker_host.app_config = None
        select_worker_host.ec2_client = None

    @patch('select_worker_host.Configuration')
    @patch('boto3.client')
    def test_select_worker_host_given_no_hosts(self: TestCase,
                                               mocked_client: MagicMock,
                                               mocked_configuration: MagicMock):
        mocked_app_config = mocked_configuration.return_value

        with self.assertRaises(RuntimeError) as context:
            select_worker_host.select(None, None)

        mocked_configuration.assert_called_once()
        mocked_client.assert_called_once_with('ec2', config=mocked_app_config.get_boto_config())
        self.assertEqual(context.expected, RuntimeError)
        self.assertEqual(str(context.exception), 'No usable EC2 instances found')

    @patch('select_worker_host.Configuration')
    @patch('boto3.client')
    def test_select_worker_host_given_one_host(self: TestCase,
                                               mocked_client: MagicMock,
                                               mocked_configuration: MagicMock):
        mocked_app_config = mocked_configuration.return_value
        mocked_ec2_client: MagicMock = mocked_client.return_value
        mocked_paginator: MagicMock = mocked_ec2_client.get_paginator.return_value
        mocked_paginator.paginate.return_value = [
            {
                'Reservations': [
                    {
                        'Instances': [
                            {
                                'InstanceId': 'instance-0'
                            },
                        ]
                    }
                ]
            }
        ]

        response = select_worker_host.select(None, None)

        mocked_configuration.assert_called_once()
        mocked_client.assert_called_once_with('ec2', config=mocked_app_config.get_boto_config())
        mocked_ec2_client.get_paginator.assert_called_once_with('describe_instances')
        mocked_paginator.paginate.assert_called_once_with(Filters=[
            {
                'Name': 'tag:Name',
                'Values': ['TerraformEngineExecutionInstance']
            },
            {
                'Name': 'instance-state-name',
                'Values': ['running']
            }
        ])

        self.assertEqual(response, {'instanceId': 'instance-0'})

    @patch('select_worker_host.Configuration')
    @patch('boto3.client')
    def test_select_worker_host_given_two_hosts(self: TestCase,
                                                mocked_client: MagicMock,
                                                mocked_configuration: MagicMock):
        mocked_app_config = mocked_configuration.return_value
        mocked_ec2_client: MagicMock = mocked_client.return_value
        mocked_paginator: MagicMock = mocked_ec2_client.get_paginator.return_value
        mocked_paginator.paginate.return_value = [
            {
                'Reservations': [
                    {
                        'Instances': [
                            {
                                'InstanceId': 'instance-0'
                            },
                            {
                                'InstanceId': 'instance-1'
                            },
                        ]
                    }
                ]
            }
        ]

        response = select_worker_host.select(None, None)

        mocked_configuration.assert_called_once()
        mocked_client.assert_called_once_with('ec2', config=mocked_app_config.get_boto_config())
        mocked_ec2_client.get_paginator.assert_called_once_with('describe_instances')
        mocked_paginator.paginate.assert_called_once_with(Filters=[
            {
                'Name': 'tag:Name',
                'Values': ['TerraformEngineExecutionInstance']
            },
            {
                'Name': 'instance-state-name',
                'Values': ['running']
            }
        ])

        instance_id = response['instanceId']
        self.assertRegex(instance_id, 'instance-\d')

    @patch('select_worker_host.Configuration')
    @patch('boto3.client')
    def test_select_worker_host_given_three_hosts(self: TestCase,
                                                  mocked_client: MagicMock,
                                                  mocked_configuration: MagicMock):
        mocked_app_config = mocked_configuration.return_value
        mocked_ec2_client: MagicMock = mocked_client.return_value
        mocked_paginator: MagicMock = mocked_ec2_client.get_paginator.return_value
        mocked_paginator.paginate.return_value = [
            {
                'Reservations': [
                    {
                        'Instances': [
                            {
                                'InstanceId': 'instance-0'
                            },
                            {
                                'InstanceId': 'instance-1'
                            },
                        ]
                    }
                ]
            },
            {
                'Reservations': [
                    {
                        'Instances': [
                            {
                                'InstanceId': 'instance-3'
                            },
                        ]
                    }
                ]
            }
        ]

        response = select_worker_host.select(None, None)

        mocked_configuration.assert_called_once()
        mocked_client.assert_called_once_with('ec2', config=mocked_app_config.get_boto_config())
        mocked_ec2_client.get_paginator.assert_called_once_with('describe_instances')
        mocked_paginator.paginate.assert_called_once_with(Filters=[
            {
                'Name': 'tag:Name',
                'Values': ['TerraformEngineExecutionInstance']
            },
            {
                'Name': 'instance-state-name',
                'Values': ['running']
            }
        ])

        instance_id = response['instanceId']
        self.assertRegex(instance_id, 'instance-\d')

    @patch('select_worker_host.Configuration')
    @patch('boto3.client')
    def test_select_worker_host_given_ec2_error(self: TestCase,
                                                mocked_client: MagicMock,
                                                mocked_configuration: MagicMock):
        mocked_app_config = mocked_configuration.return_value
        mocked_ec2_client: MagicMock = mocked_client.return_value
        mocked_paginator: MagicMock = mocked_ec2_client.get_paginator.return_value

        error_response = {
            'Error': {
                'Message': 'Some EC2 4XX or 5XX error'
            },
            'ResponseMetadata': {
                'RequestId': 'some-random-uuid'
            }
        }

        mocked_client_error = ClientError(
            operation_name='describe_instances',
            error_response=error_response
        )
        mocked_paginator.paginate.side_effect = mocked_client_error

        with self.assertRaises(ClientError) as context:
            select_worker_host.select(None, None)

        mocked_configuration.assert_called_once()
        mocked_client.assert_called_once_with('ec2', config=mocked_app_config.get_boto_config())
        mocked_ec2_client.get_paginator.assert_called_once_with('describe_instances')
        mocked_paginator.paginate.assert_called_once_with(Filters=[
            {
                'Name': 'tag:Name',
                'Values': ['TerraformEngineExecutionInstance']
            },
            {
                'Name': 'instance-state-name',
                'Values': ['running']
            }
        ])

        self.assertEqual(context.expected, ClientError)
        self.assertEqual(str(context.exception), str(mocked_client_error))


if __name__ == '__main__':
    main()

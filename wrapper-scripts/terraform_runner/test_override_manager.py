import glob
import os
import json
import unittest
from terraform_runner import override_manager


class TestOverrideManager(unittest.TestCase):
    TMP_WORKSPACE_DIR = '/tmp'
    OVERRIDE_FILES_PATTERN = '*.tf.json'

    def test_write_backend_override_happy_path(self):
        # arrange
        provisioned_product_descriptor = 'account-id/pp-id'
        state_bucket = 'state-bucket'
        state_region = 'us-west-2'
        expected_backend_override = {
            'terraform': {
                'backend': {
                    's3': {
                        'bucket': f'{state_bucket}',
                        'key': f'{provisioned_product_descriptor}',
                        'region': f'{state_region}'
                    }
                }
            }
        }

        # act
        override_manager.write_backend_override(self.TMP_WORKSPACE_DIR,
                                                provisioned_product_descriptor, state_bucket, state_region)
        with open(f'{self.TMP_WORKSPACE_DIR}/{override_manager.BACKEND_FILE_NAME}', 'r') as json_file:
            actual_backend_override = json.load(json_file)

        # assert
        self.assertEqual(expected_backend_override, actual_backend_override)

    def test_write_provider_override_happy_path(self):
        # arrange
        provisioned_product_descriptor = 'account-id/pp-id'
        launch_role_arn = 'role-arn'
        region = 'us-east-1'
        tags = [{'key': 'k1', 'value': 'v1'}, {'key': 'k2', 'value': 'v2'}]
        expected_provider_override = {
            'provider': {
                'aws': {
                    'region': f'{region}',
                    'assume_role': {
                        'role_arn': f'{launch_role_arn}',
                        'session_name': f'{provisioned_product_descriptor}'.replace('/', '-')
                    },
                    'default_tags': {
                        'tags': {'k1': 'v1', 'k2': 'v2'}
                    }
                }
            }
        }

        # act
        override_manager.write_provider_override(self.TMP_WORKSPACE_DIR,
                                                 provisioned_product_descriptor, launch_role_arn, region, tags)
        with open(f'{self.TMP_WORKSPACE_DIR}/{override_manager.PROVIDER_FILE_NAME}', 'r') as json_file:
            actual_provider_override = json.load(json_file)

        # assert
        self.assertEqual(expected_provider_override, actual_provider_override)

    def test_write_provider_override_long_pp_descriptor(self):
        # arrange
        provisioned_product_descriptor = 'p' * 1000
        expected_session_name = 'p' * override_manager.MAX_SESSION_NAME_LENGTH
        launch_role_arn = 'role-arn'
        region = 'us-east-1'
        tags = [{'key': 'k1', 'value': 'v1'}, {'key': 'k2', 'value': 'v2'}]
        expected_provider_override = {
            'provider': {
                'aws': {
                    'region': f'{region}',
                    'assume_role': {
                        'role_arn': f'{launch_role_arn}',
                        'session_name': f'{expected_session_name}'
                    },
                    'default_tags': {
                        'tags': {'k1': 'v1', 'k2': 'v2'}
                    }
                }
            }
        }

        # act
        override_manager.write_provider_override(self.TMP_WORKSPACE_DIR,
                                                 provisioned_product_descriptor, launch_role_arn, region, tags)
        with open(f'{self.TMP_WORKSPACE_DIR}/{override_manager.PROVIDER_FILE_NAME}', 'r') as json_file:
            actual_provider_override = json.load(json_file)

        # assert
        self.assertEqual(expected_provider_override, actual_provider_override)

    def test_write_provider_override_no_tags(self):
        # arrange
        provisioned_product_descriptor = 'account-id/pp-id'
        launch_role_arn = 'role-arn'
        region = 'us-east-1'
        tags = None
        expected_provider_override = {
            'provider': {
                'aws': {
                    'region': f'{region}',
                    'assume_role': {
                        'role_arn': f'{launch_role_arn}',
                        'session_name': f'{provisioned_product_descriptor}'.replace('/', '-')
                    },
                    'default_tags': {'tags': {}}
                }
            }
        }

        # act
        override_manager.write_provider_override(self.TMP_WORKSPACE_DIR,
                                                 provisioned_product_descriptor, launch_role_arn, region, tags)
        with open(f'{self.TMP_WORKSPACE_DIR}/{override_manager.PROVIDER_FILE_NAME}', 'r') as json_file:
            actual_provider_override = json.load(json_file)

        # assert
        self.assertEqual(expected_provider_override, actual_provider_override)

    def test_write_provider_override_empty_tags(self):
        # arrange
        provisioned_product_descriptor = 'account-id/pp-id'
        launch_role_arn = 'role-arn'
        region = 'us-east-1'
        tags = {}
        expected_provider_override = {
            'provider': {
                'aws': {
                    'region': f'{region}',
                    'assume_role': {
                        'role_arn': f'{launch_role_arn}',
                        'session_name': f'{provisioned_product_descriptor}'.replace('/', '-')
                    },
                    'default_tags': {'tags': {}}
                }
            }
        }

        # act
        override_manager.write_provider_override(self.TMP_WORKSPACE_DIR,
                                                 provisioned_product_descriptor, launch_role_arn, region, tags)
        with open(f'{self.TMP_WORKSPACE_DIR}/{override_manager.PROVIDER_FILE_NAME}', 'r') as json_file:
            actual_provider_override = json.load(json_file)

        # assert
        self.assertEqual(expected_provider_override, actual_provider_override)

    def test_write_variable_override_happy_path(self):
        # arrange
        variables = [
            {'key': 'key1', 'value': 'value1'},
            {'key': 'key2', 'value': 'value2'}
        ]
        expected_variable_override = {
            'variable': {
                'key1': {'default': 'value1'},
                'key2': {'default': 'value2'}
            }
        }

        # act
        override_manager.write_variable_override(self.TMP_WORKSPACE_DIR, variables)
        with open(f'{self.TMP_WORKSPACE_DIR}/{override_manager.VARIABLE_FILE_NAME}', 'r') as json_file:
            actual_variable_override = json.load(json_file)

        # assert
        self.assertEqual(expected_variable_override, actual_variable_override)

    def test_write_variable_override_with_complex_type_happy_path(self):
        # arrange
        complex_type_value = {
            'nested_key_1': 'nested_value_1',
            'nested_key_2': 'nested_value_2'
        }
        variables = [
            {'key': 'key1', 'value': 'value1'},
            {'key': 'key2', 'value': json.dumps(complex_type_value)}
        ]
        expected_variable_override = {
            'variable': {
                'key1': {'default': 'value1'},
                'key2': {'default': complex_type_value}
            }
        }

        # act
        override_manager.write_variable_override(self.TMP_WORKSPACE_DIR, variables)
        with open(f'{self.TMP_WORKSPACE_DIR}/{override_manager.VARIABLE_FILE_NAME}', 'r') as json_file:
            actual_variable_override = json.load(json_file)

        # assert
        self.assertEqual(expected_variable_override, actual_variable_override)

    def test_write_variable_override_no_variables(self):
        # arrange
        variables = None

        # act
        override_manager.write_variable_override(self.TMP_WORKSPACE_DIR, variables)

        # assert
        self.assertFalse(
            os.path.exists(f'{self.TMP_WORKSPACE_DIR}/{override_manager.VARIABLE_FILE_NAME}'))

    def test_write_variable_override_empty_variables(self):
        # arrange
        variables = {}

        # act
        override_manager.write_variable_override(self.TMP_WORKSPACE_DIR, variables)

        # assert
        self.assertFalse(
            os.path.exists(f'{self.TMP_WORKSPACE_DIR}/{override_manager.VARIABLE_FILE_NAME}'))

    def tearDown(self):
        # Remove temp files after each test
        override_files = glob.glob(f'{self.TMP_WORKSPACE_DIR}/{self.OVERRIDE_FILES_PATTERN}')
        for override_file in override_files:
            os.remove(override_file)


if __name__ == '__main__':
    unittest.main()

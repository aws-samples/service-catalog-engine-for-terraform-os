import unittest
from unittest.mock import Mock, patch
from terraform_runner.artifact_manager import download_artifact, ROLE_SESSION_NAME


class TestArtifactManager(unittest.TestCase):

    @patch('terraform_runner.artifact_manager.boto3.client')
    @patch('tarfile.open')
    @patch('terraform_runner.artifact_manager.glob')
    def test_download_artifact_happy_path(self, mock_glob, mock_tarfile_open, mock_client):
        # arrange
        mock_sts = Mock()
        mock_s3 = Mock()
        mock_client.side_effect = [mock_sts, mock_s3]
        mock_credentials = {
            'AccessKeyId': 'access-key',
            'SecretAccessKey': 'secret-key',
            'SessionToken': 'session-token'
        }
        mock_assume_role_response = {'Credentials': mock_credentials}
        mock_sts.assume_role.return_value = mock_assume_role_response

        launch_role_arn = 'launch-role-arn'
        artifact_bucket = 'artifact-bucket'
        artifact_key = 'artifact'
        artifact_path = f's3://{artifact_bucket}/{artifact_key}'
        workspace_dir = 'workspace/dir'
        local_file = f'{workspace_dir}/artifact.local'

        mock_glob.return_value = ['mock.tf']

        # act
        download_artifact(launch_role_arn, artifact_path, workspace_dir)

        # assert
        mock_sts.assume_role.assert_called_once_with(RoleArn=launch_role_arn,
                                                     RoleSessionName=ROLE_SESSION_NAME)
        mock_client.assert_called_with('s3',
                                       aws_access_key_id=mock_credentials['AccessKeyId'],
                                       aws_secret_access_key=mock_credentials['SecretAccessKey'],
                                       aws_session_token=mock_credentials['SessionToken'])
        mock_s3.download_file.assert_called_once_with(artifact_bucket, artifact_key,
                                                      local_file)
        mock_tarfile_open.assert_called_once_with('artifact.local')

    @patch('terraform_runner.artifact_manager.boto3.client')
    @patch('tarfile.open')
    def test_download_artifact_tarfile_open_exception(self, mock_tarfile_open, mock_client):
        # arrange
        mock_tarfile_open.side_effect = Exception('mock exception')

        mock_sts = Mock()
        mock_s3 = Mock()
        mock_client.side_effect = [mock_sts, mock_s3]
        mock_credentials = {
            'AccessKeyId': 'access-key',
            'SecretAccessKey': 'secret-key',
            'SessionToken': 'session-token'
        }
        mock_assume_role_response = {'Credentials': mock_credentials}
        mock_sts.assume_role.return_value = mock_assume_role_response

        launch_role_arn = 'launch-role-arn'
        artifact_bucket = 'artifact-bucket'
        artifact_key = 'artifact.tar.gz'
        artifact_path = f's3://{artifact_bucket}/{artifact_key}'
        workspace_dir = 'workspace/dir'
        local_file = f'{workspace_dir}/artifact.local'

        # act
        with self.assertRaises(RuntimeError) as context:
            download_artifact(launch_role_arn, artifact_path, workspace_dir)

        # assert
        mock_sts.assume_role.assert_called_once_with(RoleArn=launch_role_arn,
                                                     RoleSessionName=ROLE_SESSION_NAME)
        mock_client.assert_called_with('s3',
                                       aws_access_key_id=mock_credentials['AccessKeyId'],
                                       aws_secret_access_key=mock_credentials['SecretAccessKey'],
                                       aws_session_token=mock_credentials['SessionToken'])
        mock_s3.download_file.assert_called_once_with(artifact_bucket, artifact_key,
                                                      local_file)
        mock_tarfile_open.assert_called_once_with('artifact.local')
        self.assertEqual(context.expected, RuntimeError)
        self.assertEqual(context.exception.args[0], f'Could not extract files from {artifact_path}: mock exception')

    @patch('terraform_runner.artifact_manager.boto3.client')
    def test_download_artifact_path_has_no_bucket(self, mock_client):
        # arrange
        launch_role_arn = 'launch-role-arn'
        artifact_path = '/test-data/foo.tf'
        workspace_dir = 'workspace/dir'

        # act and assert
        with self.assertRaises(RuntimeError) as context:
            download_artifact(launch_role_arn, artifact_path, workspace_dir)
        self.assertEqual(context.expected, RuntimeError)
        self.assertTrue(context.exception.args[0].startswith(f'Invalid artifact path {artifact_path}'))

    @patch('terraform_runner.artifact_manager.boto3.client')
    def test_download_artifact_path_has_no_key(self, mock_client):
        # arrange
        launch_role_arn = 'launch-role-arn'
        artifact_path = 's3://test-bucket'
        workspace_dir = 'workspace/dir'

        # act and assert
        with self.assertRaises(RuntimeError) as context:
            download_artifact(launch_role_arn, artifact_path, workspace_dir)
        self.assertEqual(context.expected, RuntimeError)
        self.assertTrue(context.exception.args[0].startswith(f'Invalid artifact path {artifact_path}'))

    @patch('terraform_runner.artifact_manager.boto3.client')
    @patch('tarfile.open')
    @patch('terraform_runner.artifact_manager.glob')
    def test_download_artifact_no_terraform_files(self, mock_glob, mock_tarfile_open, mock_client):
        # arrange
        mock_sts = Mock()
        mock_s3 = Mock()
        mock_client.side_effect = [mock_sts, mock_s3]
        mock_credentials = {
            'AccessKeyId': 'access-key',
            'SecretAccessKey': 'secret-key',
            'SessionToken': 'session-token'
        }
        mock_assume_role_response = {'Credentials': mock_credentials}
        mock_sts.assume_role.return_value = mock_assume_role_response

        launch_role_arn = 'launch-role-arn'
        artifact_bucket = 'artifact-bucket'
        artifact_key = 'artifact'
        artifact_path = f's3://{artifact_bucket}/{artifact_key}'
        workspace_dir = 'workspace/dir'
        local_file = f'{workspace_dir}/artifact.local'

        mock_glob.return_value = []

        # act
        with self.assertRaises(RuntimeError) as context:
            download_artifact(launch_role_arn, artifact_path, workspace_dir)

        # assert
        mock_sts.assume_role.assert_called_once_with(RoleArn=launch_role_arn,
                                                     RoleSessionName=ROLE_SESSION_NAME)
        mock_client.assert_called_with('s3',
                                       aws_access_key_id=mock_credentials['AccessKeyId'],
                                       aws_secret_access_key=mock_credentials['SecretAccessKey'],
                                       aws_session_token=mock_credentials['SessionToken'])
        mock_s3.download_file.assert_called_once_with(artifact_bucket, artifact_key,
                                                      local_file)
        mock_tarfile_open.assert_called_once_with('artifact.local')

        self.assertEqual(context.expected, RuntimeError)
        self.assertEqual(str(context.exception), 'No .tf files found. Nothing to parse. Make sure the root directory of the Terraform open source configuration file contains the .tf files for the root module.')


if __name__ == '__main__':
    unittest.main()

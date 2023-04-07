from glob import glob
import tarfile

import boto3
from botocore.exceptions import ClientError

# Constants
ROLE_SESSION_NAME = 'TerraformLaunchRole'
LOCAL_ARTIFACT_FILE = 'artifact.local'
REQUIRED_FILES_PATTERN = '*.tf'
NO_REQUIRED_FILES_FOUND_MESSAGE = 'No .tf files found. Nothing to parse. Make sure the root directory of the Terraform open source configuration file contains the .tf files for the root module.'

# Boto exception keys
RESPONSE_METADATA_KEY = "ResponseMetadata"
REQUEST_ID_KEY = "RequestId"


def __get_s3_client(launch_role_arn):
    sts = boto3.client('sts')
    assume_role_result = sts.assume_role(RoleArn=launch_role_arn,
                                         RoleSessionName=ROLE_SESSION_NAME)
    credentials = assume_role_result['Credentials']
    return boto3.client('s3',
                        aws_access_key_id=credentials['AccessKeyId'],
                        aws_secret_access_key=credentials['SecretAccessKey'],
                        aws_session_token=credentials['SessionToken'])

def __validate_required_files_exist(workspace_dir):
    files = glob(f'{workspace_dir}/{REQUIRED_FILES_PATTERN}')
    if not files:
        raise RuntimeError(NO_REQUIRED_FILES_FOUND_MESSAGE)

def download_artifact(launch_role_arn, artifact_path, workspace_dir):
    # Extract bucket, key, and file name from the path. This will be the S3 URI.
    # Example: s3://my-bucket/test-data/main.tar.gz
    try:
        bucket = artifact_path.split('/')[2]
        key = artifact_path.split('/', 3)[3]
    except IndexError as e:
        raise RuntimeError(f'Invalid artifact path {artifact_path}: {e}')

    try:
        s3 = __get_s3_client(launch_role_arn)
        s3.download_file(bucket, key, f'{workspace_dir}/{LOCAL_ARTIFACT_FILE}')
    except ClientError as e:
        message = f'Failed to execute API: {e.operation_name} with request Id: {e.response[RESPONSE_METADATA_KEY][REQUEST_ID_KEY]}: {e}'
        raise RuntimeError(
            f'Could not download artifact {artifact_path} using launch role {launch_role_arn}: {message}')
    except Exception as e:
        raise RuntimeError(f'Could not download artifact {artifact_path} using launch role {launch_role_arn}: {e}')

    try:
        with   tarfile.open(LOCAL_ARTIFACT_FILE) as file_handle:
            file_handle.extractall(workspace_dir)
    except Exception as e:
        raise RuntimeError(f'Could not extract files from {artifact_path}: {e}')

    __validate_required_files_exist(workspace_dir)

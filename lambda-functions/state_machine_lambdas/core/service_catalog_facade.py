import logging
import os
import uuid
from enum import Enum

from core.configuration import Configuration


log = logging.getLogger()
log.setLevel(logging.INFO)


### We must force Lambdas that use this class to use the local version of boto3/botocore 
### because we need the latest release of the Service Catalog SDK.
###
### This is required because Lambda runtime environments lag behind on the SDK releases. 
###
### This code assumes that boto3 and botocore have been installed in the designated local directory.
### See the Readme and the deploy-tre.sh script for details.
###
### We will be able to remove this code once we are certain that Lambda runtime environments are using the minimum required versions across all regions.
import sys

LAMBDA_TASK_ROOT = 'LAMBDA_TASK_ROOT'
LOCAL_INSTALL_DIR = 'state_machine_lambdas'

if LAMBDA_TASK_ROOT in os.environ:
    lambda_task_root = os.environ[LAMBDA_TASK_ROOT]
    log.info(f'{LAMBDA_TASK_ROOT} was found in os.environ: {lambda_task_root}. Now modifying sys.path to use the local versions of boto3/botocore instead of the versions provided by the Lambda runtime environment.')

    log.info(f'sys.path before modification: {str(sys.path)}')
    sys.path.insert(0, f'{lambda_task_root}/{LOCAL_INSTALL_DIR}')
    log.info(f'sys.path after modification: {str(sys.path)}')

else:
    log.info(f'{LAMBDA_TASK_ROOT} was not found in os.environ. No modifications were made to sys.path to load the local versions of boto3/botocore. this indicates that this code is not running in a Lambda environment.')

import boto3
log.info(f'boto3 version: {boto3.__version__}')
### End of code to use the local build of boto3/botocore


# Constants
TRUE = 'true'
SERVICE_CATALOG_VERIFY_SSL = 'SERVICE_CATALOG_VERIFY_SSL'
SERVICE_CATALOG_ENDPOINT = 'SERVICE_CATALOG_ENDPOINT'


class Status(Enum):
    SUCCEEDED = 0
    FAILED = 1

class ServiceCatalogFacade:

    def __init__(self, app_config: Configuration):
        self.__service_catalog_client = self.__get_service_catalog_client(app_config)

    def __get_service_catalog_client(self, app_config: Configuration):
        verify = SERVICE_CATALOG_VERIFY_SSL not in os.environ or os.environ[SERVICE_CATALOG_VERIFY_SSL] == TRUE
        log.info(f'Constructing Service Catalog client: verify={verify}')

        if SERVICE_CATALOG_ENDPOINT in os.environ and os.environ[SERVICE_CATALOG_ENDPOINT]:
            endpoint_url = os.environ[SERVICE_CATALOG_ENDPOINT]
            log.info(f'Constructing Service Catalog client with overridden endpoint={endpoint_url}')
            return boto3.client('servicecatalog',
                verify = verify,
                endpoint_url = endpoint_url,
                config = app_config.get_boto_config())
        else:
            log.info('Constructing Service Catalog client with default endpoint')
            return boto3.client('servicecatalog',
                verify = verify,
                config = app_config.get_boto_config())

    def __log_response(self, response):
        log.info(f'Notified service catalog of workflow results via request Id: '
                 f'{response["ResponseMetadata"]["RequestId"]}')

    def notify_provision_succeeded(self, *,
        workflow_token: str,
        record_id: str,
        tracer_tag_key: str,
        tracer_tag_value: str,
        outputs: list
        ):

        response = self.__service_catalog_client.notify_provision_product_engine_workflow_result(
            WorkflowToken = workflow_token,
                RecordId = record_id,
                Status = Status.SUCCEEDED.name,
                ResourceIdentifier = {
                    'UniqueTag': {
                        'Key': tracer_tag_key,
                        'Value': tracer_tag_value
                    }
                },
                Outputs = outputs,
                IdempotencyToken=str(uuid.uuid4())
            )
        self.__log_response(response)

    def notify_provision_failed(self, *,
        workflow_token: str,
        record_id: str,
        failure_reason: str,
        tracer_tag_key: str,
        tracer_tag_value: str,
        outputs: str
        ):

        response = self.__service_catalog_client.notify_provision_product_engine_workflow_result(
            WorkflowToken = workflow_token,
                RecordId = record_id,
                Status = Status.FAILED.name,
                FailureReason = failure_reason,
                ResourceIdentifier = {
                    'UniqueTag': {
                        'Key': tracer_tag_key,
                        'Value': tracer_tag_value
                    }
                },
                Outputs = outputs,
                IdempotencyToken=str(uuid.uuid4())
            )
        self.__log_response(response)

    def notify_update_succeeded(self, *,
        workflow_token: str,
        record_id: str,
        outputs: list
        ):

        response = self.__service_catalog_client.notify_update_provisioned_product_engine_workflow_result(
            WorkflowToken = workflow_token,
            RecordId = record_id,
            Status = Status.SUCCEEDED.name,
            Outputs = outputs,
            IdempotencyToken=str(uuid.uuid4())
        )
        self.__log_response(response)

    def notify_update_failed(self, *,
        workflow_token: str,
        record_id: str,
        failure_reason: str,
        outputs: str
        ):

        response = self.__service_catalog_client.notify_update_provisioned_product_engine_workflow_result(
            WorkflowToken = workflow_token,
            RecordId = record_id,
            Status = Status.FAILED.name,
            FailureReason = failure_reason,
            Outputs = outputs,
            IdempotencyToken=str(uuid.uuid4())
        )
        self.__log_response(response)

    def notify_terminate_succeeded(self, *,
        workflow_token: str,
        record_id: str,
        ):

        response = self.__service_catalog_client.notify_terminate_provisioned_product_engine_workflow_result(
            WorkflowToken = workflow_token,
                RecordId = record_id,
                Status = Status.SUCCEEDED.name,
                IdempotencyToken=str(uuid.uuid4())
            )
        self.__log_response(response)

    def notify_terminate_failed(self, *,
        workflow_token: str,
        record_id: str,
        failure_reason: str
        ):

        response = self.__service_catalog_client.notify_terminate_provisioned_product_engine_workflow_result(
            WorkflowToken = workflow_token,
                RecordId = record_id,
                Status = Status.FAILED.name,
                FailureReason = failure_reason,
                IdempotencyToken=str(uuid.uuid4())
            )
        self.__log_response(response)

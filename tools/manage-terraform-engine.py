#!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""Provides a command-line interface for administering a deployed Terraform Reference Engine environment.

Args:
    --action, -a: (Optional) A string that represents the action to execute against the Terraform Reference
        Engine. Must be one of {'start', 'status', 'stop', 'replace'}. Defaults to 'status'.

    --region, -r: (Optional) A string that represents the AWS region name in which the Terraform
        Reference Engine is deployed. If not specified, the module will attempt to determine the correct
        region from runtime environment variables: "AWS_DEFAULT_REGION", "AWS_PROFILE_REGION", and
        "AWS_REGION". Defaults to `None`.

    --auto-approve: (Optional) A flag that instructs the module to not require interactive approval when
        making changes to the Terraform Reference Engine. By default, interactive approval is required.

    --verbose, -v: (Optional) A flag that increases the logging verbosity of the module. The flag is
        cumulative and if specified more than once will result in debug logging for not only the module
        but its underlying AWS SDK libraries as well.

    --instance-name: (Optional) The value assigned to the Name tag of the Terraform Reference Engine
        execution instances. Defaults to 'TerraformEngineExecutionInstance'.

    --autoscaling-group-name: (Optional) The name of the Terraform Reference Engine auto scaling group.
        Defaults to 'TerraformAutoscalingGroup'.

Example:
    # Check the current status of the Terraform Reference Engine.
    python3 ./bin/bash/manage-terraform-engine.py \
       --action status \
       --region us-east-2

    2023-07-13T17:59:38Z [INFO] - Checking the status of the Terraform Reference Engine in AWS account '123456789012' and region 'us-east-2'
    2023-07-13T17:59:40Z [INFO] - Terraform Reference Engine Status: 'Enabled'
    2023-07-13T17:59:40Z [INFO] - Total execution time: 3s

Example:
    # Stop the Terraform Reference Engine from processing any new TRE requests and gracefully terminate all
    # TRE execution instances after waiting for all in-flight TRE requests to complete.
    python3 ./bin/bash/manage-terraform-engine.py \
       --action stop \
       --region us-east-2

    2023-07-13T18:03:34Z [INFO] - Checking the status of the Terraform Reference Engine in AWS account '123456789012' and region 'us-east-2'
    2023-07-13T18:03:35Z [INFO] - Terraform Reference Engine Status: 'Enabled'
    2023-07-13T18:03:35Z [WARNING] - You have requested to change the status of the Terraform Reference Engine in AWS account '123456789012' and region 'us-east-2' to 'Disabled'
    Do you want to continue? [Y/n]: Y
    2023-07-13T18:03:40Z [INFO] - Stopping the Terraform Reference Engine from processing new requests
    2023-07-13T18:03:40Z [INFO] - Disabling the event source '9b220401-3da6-43d5-946e-c654e01bcdf5' for TRE function 'TerraformEngineProvisioningHandlerLambda'
    2023-07-13T18:03:41Z [INFO] - Waiting for event source '9b220401-3da6-43d5-946e-c654e01bcdf5' to reach the desired state 'Disabled'
    2023-07-13T18:03:56Z [INFO] - The event source '9b220401-3da6-43d5-946e-c654e01bcdf5' for TRE function 'TerraformEngineProvisioningHandlerLambda' has been successfully disabled
    2023-07-13T18:03:56Z [INFO] - Disabling the event source 'e5ba8247-2b6e-41ee-a059-1d6f34f0f3e1' for TRE function 'TerraformEngineProvisioningHandlerLambda'
    2023-07-13T18:03:57Z [INFO] - Waiting for event source 'e5ba8247-2b6e-41ee-a059-1d6f34f0f3e1' to reach the desired state 'Disabled'
    2023-07-13T18:04:12Z [INFO] - The event source 'e5ba8247-2b6e-41ee-a059-1d6f34f0f3e1' for TRE function 'TerraformEngineProvisioningHandlerLambda' has been successfully disabled
    2023-07-13T18:04:12Z [INFO] - Disabling the event source '5ec315c4-26c8-4596-a588-09bc5aff0c81' for TRE function 'TerraformEngineTerminateHandlerLambda'
    2023-07-13T18:04:13Z [INFO] - Waiting for event source '5ec315c4-26c8-4596-a588-09bc5aff0c81' to reach the desired state 'Disabled'
    2023-07-13T18:04:23Z [INFO] - The event source '5ec315c4-26c8-4596-a588-09bc5aff0c81' for TRE function 'TerraformEngineTerminateHandlerLambda' has been successfully disabled
    2023-07-13T18:04:23Z [INFO] - Waiting for any currently running Terraform Reference Engine executions to complete
    2023-07-13T18:04:24Z [INFO] - Initiating a terminate operation for the following TRE execution instances: ['i-01cdd04a86197e492']
    2023-07-13T18:04:25Z [INFO] - Suspending the following scaling processes for auto scaling group 'TerraformAutoscalingGroup': ['Launch', 'ReplaceUnhealthy']
    2023-07-13T18:04:25Z [INFO] - Successfully initiated termination for 1 TRE execution instances
    2023-07-13T18:04:25Z [INFO] - Waiting for TRE execution instances to reach one of the following desired states: ['terminated']
    2023-07-13T18:04:56Z [INFO] - All TRE execution instances have reached one of the desired states
    2023-07-13T18:04:56Z [INFO] - Waiting for the number of TRE execution instances in the auto scaling group 'TerraformAutoscalingGroup' to reach 0
    2023-07-13T18:05:12Z [INFO] - The number of TRE execution instances in the auto scaling group 'TerraformAutoscalingGroup' is 0
    2023-07-13T18:05:12Z [INFO] - Checking the status of the Terraform Reference Engine in AWS account '123456789012' and region 'us-east-2'
    2023-07-13T18:05:12Z [INFO] - Terraform Reference Engine Status: 'Disabled'
    2023-07-13T18:05:12Z [INFO] - The Terraform Reference Engine has been successfully stopped, any new requests will remain in their SQS queues until restarted or they timeout
    2023-07-13T18:05:12Z [INFO] - Total execution time: 99s

Example:
    # Start the Terraform Reference Engine execution instances and resume processing of new TRE requests,
    # do not require interactive approval.
    python3 ./bin/bash/manage-terraform-engine.py \
       --action start \
       --region us-east-2 \
       --auto-approve

    2023-07-13T18:07:53Z [INFO] - Checking the status of the Terraform Reference Engine in AWS account '123456789012' and region 'us-east-2'
    2023-07-13T18:07:53Z [INFO] - Terraform Reference Engine Status: 'Disabled'
    2023-07-13T18:07:53Z [INFO] - Starting Terraform Reference Engine execution instances
    2023-07-13T18:07:53Z [INFO] - Resuming the following scaling processes for auto scaling group 'TerraformAutoscalingGroup': ['Launch', 'ReplaceUnhealthy']
    2023-07-13T18:07:54Z [INFO] - Waiting for TRE execution instances to reach one of the following desired states: ['running']
    2023-07-13T18:08:39Z [INFO] - All TRE execution instances have reached one of the desired states
    2023-07-13T18:08:39Z [INFO] - Waiting for the number of TRE execution instances in the auto scaling group 'TerraformAutoscalingGroup' to reach 1
    2023-07-13T18:08:40Z [INFO] - The number of TRE execution instances in the auto scaling group 'TerraformAutoscalingGroup' is 1
    2023-07-13T18:08:40Z [INFO] - Resuming the processing of new requests by the Terraform Reference Engine
    2023-07-13T18:08:40Z [INFO] - Enabling the event source '9b220401-3da6-43d5-946e-c654e01bcdf5' for TRE function 'TerraformEngineProvisioningHandlerLambda'
    2023-07-13T18:08:40Z [INFO] - Waiting for event source '9b220401-3da6-43d5-946e-c654e01bcdf5' to reach the desired state 'Enabled'
    2023-07-13T18:09:01Z [INFO] - The event source '9b220401-3da6-43d5-946e-c654e01bcdf5' for TRE function 'TerraformEngineProvisioningHandlerLambda' has been successfully enabled
    2023-07-13T18:09:01Z [INFO] - Enabling the event source 'e5ba8247-2b6e-41ee-a059-1d6f34f0f3e1' for TRE function 'TerraformEngineProvisioningHandlerLambda'
    2023-07-13T18:09:02Z [INFO] - Waiting for event source 'e5ba8247-2b6e-41ee-a059-1d6f34f0f3e1' to reach the desired state 'Enabled'
    2023-07-13T18:09:17Z [INFO] - The event source 'e5ba8247-2b6e-41ee-a059-1d6f34f0f3e1' for TRE function 'TerraformEngineProvisioningHandlerLambda' has been successfully enabled
    2023-07-13T18:09:17Z [INFO] - Enabling the event source '5ec315c4-26c8-4596-a588-09bc5aff0c81' for TRE function 'TerraformEngineTerminateHandlerLambda'
    2023-07-13T18:09:18Z [INFO] - Waiting for event source '5ec315c4-26c8-4596-a588-09bc5aff0c81' to reach the desired state 'Enabled'
    2023-07-13T18:09:28Z [INFO] - The event source '5ec315c4-26c8-4596-a588-09bc5aff0c81' for TRE function 'TerraformEngineTerminateHandlerLambda' has been successfully enabled
    2023-07-13T18:09:28Z [INFO] - Checking the status of the Terraform Reference Engine in AWS account '123456789012' and region 'us-east-2'
    2023-07-13T18:09:29Z [INFO] - Terraform Reference Engine Status: 'Enabled'
    2023-07-13T18:09:29Z [INFO] - The Terraform Reference Engine has been successfully started, any new requests received or requests currently in the TRE SQS queues will be processed
    2023-07-13T18:09:29Z [INFO] - Total execution time: 98s
"""

import argparse
import datetime
import logging
import math
import os
import sys
import time
from typing import Optional, Union
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mypy_boto3_autoscaling.client import AutoScalingClient
    from mypy_boto3_autoscaling.type_defs import (
        AutoScalingGroupTypeDef,
        InstanceTypeDef,
    )
    from mypy_boto3_ec2.client import EC2Client
    from mypy_boto3_lambda import LambdaClient
    from mypy_boto3_lambda.type_defs import EventSourceMappingConfigurationTypeDef
    from mypy_boto3_stepfunctions.client import SFNClient
    from mypy_boto3_sts.client import STSClient
    from mypy_boto3_sts.type_defs import GetCallerIdentityResponseTypeDef
else:
    AutoScalingClient = object
    AutoScalingGroupTypeDef = object
    EC2Client = object
    EventSourceMappingConfigurationTypeDef = object
    GetCallerIdentityResponseTypeDef = object
    InstanceTypeDef = object
    LambdaClient = object
    SFNClient = object
    STSClient = object

import boto3


# =====================
#    Module Constants
# =====================
ACTION_START = "start"
ACTION_STATUS = "status"
ACTION_STOP = "stop"
ACTION_REPLACE = "replace"
AWS_REGION_ENV_VARS = ("AWS_DEFAULT_REGION", "AWS_PROFILE_REGION", "AWS_REGION")
DEFAULT_ASG_DESIRED_CAPACITY = 1
DEFAULT_ASG_NAME = "TerraformAutoscalingGroup"
DEFAULT_INSTANCE_NAME = "TerraformEngineExecutionInstance"
INSTANCE_STATE_RUNNING = "running"
INSTANCE_STATE_TERMINATED = "terminated"


def __check_aws_region(
    region: Optional[str] = None, raise_on_error: bool = False
) -> Optional[str]:
    """Returns the specified AWS region name if it is a valid AWS region.

    Args:
        region: The AWS region name that should be checked for validity.
        raise_on_error: If True, an exception will be raised if the region
            name fails validation. Defaults to `False`.

    Returns:
        If the supplied region name is a valid AWS region, it will be returned
        as a string. If the caller supplied a null or empty string, and the
        `raise_on_error` argument is `False`, the function will return `None`.

    Raises:
         ValueError: The supplied region name is not a valid AWS region. The
            exception will only be raised if the `raise_on_error` argument is
            `True`.
    """
    _valid_aws_regions: list[str] = boto3.session.Session().get_available_regions("sts")
    if region not in _valid_aws_regions and raise_on_error:
        raise ValueError(
            f"The specified AWS region name '{region}' must be a valid AWS region "
            f"name:\n{_valid_aws_regions}"
        )
    if region not in _valid_aws_regions:
        region = None
    return region


def __get_aws_region(args: argparse.Namespace) -> Optional[str]:
    """Gets the correct AWS region in which commands should be executed.

    Determines the correct AWS region either from user-supplied arguments
    or from the runtime environment. All region names are checked against
    the list of valid AWS regions.

    If a region was not supplied by the caller using the `--region`
    argument, the function will look for a valid AWS region in the
    environment variables defined in the `AWS_REGION_ENV_VARS` module
    constant, in ascending order of priority.

    Args:
        args: The command-line arguments supplied by the user.

    Returns:
         A string representing the validated AWS region name that should
         be used when executing commands. If no region was found, or
         none passed validation, the function returns None.
    """
    region_name: Optional[str] = None
    if args.region is not None:
        return __check_aws_region(args.region, raise_on_error=True)
    for region_env_var in AWS_REGION_ENV_VARS:
        if not os.environ.get(region_env_var):
            continue
        if not __check_aws_region(os.environ.get(region_env_var)):
            continue
        region_name = os.environ.get(region_env_var, region_name)
    return region_name


def __parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-a",
        "--action",
        help="(Optional) The action to perform against the Terraform Reference Engine. "
        f"Defaults to '{ACTION_STATUS}'.",
        choices=[ACTION_START, ACTION_STATUS, ACTION_STOP, ACTION_REPLACE],
        default=ACTION_STATUS,
    )
    parser.add_argument(
        "-r",
        "--region",
        help="(Optional) The region where the Terraform Reference Engine environment is deployed. "
        "Defaults to 'None'.",
        default=None,
    )
    parser.add_argument(
        "--auto-approve",
        help="(Optional) Do not require interactive approval for changes. Defaults to 'False'.",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--instance-name",
        help="(Optional) The name assigned to the Terraform Reference Engine execution instances. "
        f"Defaults to '{DEFAULT_INSTANCE_NAME}'.",
        default=DEFAULT_INSTANCE_NAME,
    )
    parser.add_argument(
        "--autoscaling-group-name",
        help="(Optional) The name assigned to the Terraform Reference Engine auto scaling group. "
        f"Defaults to '{DEFAULT_ASG_NAME}'.",
        default=DEFAULT_ASG_NAME,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="(Optional) Increase the verbosity of the log output.",
        action="count",
        default=0,
    )
    return parser.parse_args()


def __request_approval(message: str) -> bool:
    _approval_attempt = 0
    _valid_responses = ("y", "yes", "n", "no")
    while _approval_attempt < 3:
        logging.warning(message)
        response = input("Do you want to continue? [Y/n]: ")
        if response.lower() not in _valid_responses:
            logging.error(
                f"The confirmation must be either 'Y|Yes' or 'N|No', you entered '{response}'"
            )
            _approval_attempt += 1
            continue
        if response.lower() in ("y", "yes"):
            return True
        if response.lower() in ("n", "no"):
            break
    return False


# ================================
#    Global Module Configuration
# ================================
def __configure_logging():
    args = __parse_arguments()
    # Unless the caller maximized verbosity (e.g., -vv), suppress
    # logging from the core AWS SDK libraries.
    if args.verbose <= 1:
        logging.getLogger("boto3").setLevel(logging.CRITICAL)
        logging.getLogger("botocore").setLevel(logging.CRITICAL)
        logging.getLogger("s3transfer").setLevel(logging.CRITICAL)
        logging.getLogger("urllib3").setLevel(logging.CRITICAL)
    logging.basicConfig(
        stream=sys.stdout,
        filemode="w",
        format="%(asctime)s [%(levelname)s] - %(message)s",
        level=logging.DEBUG if args.verbose > 0 else logging.INFO,
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )
    return logging.getLogger("TerraformReferenceEngine")


logger = __configure_logging()


class TerraformReferenceEngine:
    """Provides an interface for managing the Terraform Reference Engine environment.

    Provides users with the ability to determine the current state of the Terraform
    Reference Engine (TRE) and execute administrative actions to include safely
    stopping the TRE environment from processing new requests and shutting down
    TRE execution instances or starting the TRE environment and resuming processing
    of new requests.

    Attributes:
        autoscaling_group_name: A string indicating the name of the auto scaling
            group which manages the TRE execution instances.

        instance_name: A string that represents the value assigned to the `Name`
            tag of the TRE execution instances.

        region: A string that indicates the AWS region name in which the TRE
            environment is running.
    """

    _check_interval_seconds: int = 15
    tre_handler_names: tuple[str, ...] = (
        "TerraformEngineProvisioningHandlerLambda",
        "TerraformEngineTerminateHandlerLambda",
    )
    tre_state_machine_names: tuple[str, ...] = (
        "ManageProvisionedProductStateMachine",
        "TerminateProvisionedProductStateMachine",
    )

    def __init__(
        self,
        autoscaling_group_name: str,
        instance_name: str,
        region: str,
    ):
        """Initializes an instance of the Terraform Reference Engine management interface.

        Args:
            autoscaling_group_name: Defines the name of the auto scaling group which manages
                the TRE execution instances.

            instance_name: Defines the value assigned to the `Name` tag of the TRE execution
                instances.

            region: Defines the AWS region name in which the TRE environment is deployed.

        Raises:
            RuntimeError: The Terraform Reference Engine is not deployed to the AWS account
                and region in which we are executing, or the user does not have the necessary
                permissions to describe the TRE infrastructure components.
        """
        self.autoscaling_group_name: str = autoscaling_group_name
        self.instance_name: str = instance_name
        self.region: str = region

        self._asg_client: AutoScalingClient = self._get_service_client("autoscaling")
        self._ec2_client: EC2Client = self._get_service_client("ec2")
        self._lambda_client: LambdaClient = self._get_service_client("lambda")
        self._sfn_client: SFNClient = self._get_service_client("stepfunctions")
        self._sts_client: STSClient = self._get_service_client("sts")

        self._caller_identity: Optional[GetCallerIdentityResponseTypeDef] = None
        self._autoscaling_group_data: Optional[AutoScalingGroupTypeDef] = None
        self._event_source_data: Optional[
            dict[str, list[EventSourceMappingConfigurationTypeDef]]
        ] = None

        if not self.autoscaling_group_data() or not self._get_event_source_data():
            raise RuntimeError(
                f"The AWS account '{self.account_id}' does not appear to have the Terraform "
                f"Reference Engine deployed in region '{self.region}'"
            )

    @property
    def account_id(self) -> str:
        """The 12-digit AWS account identifier in which the TRE environment is deployed."""
        if self._caller_identity is None:
            self._caller_identity = self._sts_client.get_caller_identity()
        return self._caller_identity["Account"]

    def autoscaling_group_data(
        self, force_refresh: bool = False
    ) -> Optional[AutoScalingGroupTypeDef]:
        """Returns the configuration details of the TRE auto scaling group.

        Args:
            force_refresh: If True, the method will always execute an AWS
                API call to fetch the most current configuration data,
                otherwise the cached data will be used.
        """
        if self._autoscaling_group_data is None or force_refresh:
            self._autoscaling_group_data = self._get_autoscaling_group_data()
        return self._autoscaling_group_data

    def check_status(self) -> bool:
        """Checks the current status of the core components of the TRE environment.

        Returns:
            True if the Terraform Reference Environment is configured to process new
            requests, the number of running and healthy TRE execution instances matches
            the desired number of instances, and the auto scaling group has no suspended
            processes, otherwise False.
        """
        logging.info(
            f"Checking the status of the Terraform Reference Engine in AWS account "
            f"'{self.account_id}' and region '{self.region}'"
        )
        _running_instance_count = len(
            self._get_instance_ids(check_health=True, force_refresh=False)
        )
        _desired_instance_count = self.autoscaling_group_data()["DesiredCapacity"]
        # noinspection PyTypeChecker
        _suspended_processes = [
            x["ProcessName"]
            for x in self.autoscaling_group_data()["SuspendedProcesses"]
        ]
        logging.debug(
            f"Current status of the Terraform Reference Engine components:"
            f"\n   - Account ID: {self.account_id}"
            f"\n   - AWS Region: {self.region}"
            f"\n   - Autoscaling Group Name: {self.autoscaling_group_name}"
            f"\n   - Desired TRE Instances: {_desired_instance_count}"
            f"\n   - Running TRE Instances: {_running_instance_count or None}"
            f"\n   - Suspended Scaling Processes: {_suspended_processes or None}"
            f"\n   - Request Processing Enabled: {self.request_processing_enabled()}"
        )
        return (
            _running_instance_count == _desired_instance_count
            and not _suspended_processes
            and self.request_processing_enabled()
        )

    def request_processing_enabled(self) -> bool:
        """Returns True if the TRE environment is configured to process new requests."""
        for function_name in self.tre_handler_names:
            _disabled_event_sources = self._get_event_sources(
                function_name,
                desired_state="Enabled",
                return_noncompliant_only=True,
                force_refresh=True,
            )
            if _disabled_event_sources:
                return False
        return True

    def resume_request_processing(self) -> bool:
        """Configures the TRE environment to start processing new requests."""
        result = True
        if self.request_processing_enabled():
            logging.info(
                "The Terraform Reference Engine is already configured to process new "
                "requests, skipping this step"
            )
            return True
        logging.info(
            "Resuming the processing of new requests by the Terraform Reference Engine"
        )
        for function_name, event_sources in self._get_event_source_data().items():
            result = result and self._update_event_source(
                function_name=function_name,
                event_sources=event_sources,
                event_source_enabled=True,
            )
        if not result:
            logging.error(
                "An error occurred while attempting to resume the processing of new requests by "
                "the Terraform Reference Engine, no further actions will be taken"
            )
            return False
        return result

    def start_instances(self) -> bool:
        """Initializes the TRE execution instances and waits for them to enter service."""
        logging.info("Starting Terraform Reference Engine execution instances")
        self._resume_asg_processes()
        return self._wait_for_instances(instance_state=[INSTANCE_STATE_RUNNING])

    def stop_request_processing(self) -> bool:
        """Configures the TRE environment to stop processing new requests."""
        result = True
        if not self.request_processing_enabled():
            logging.info(
                "The Terraform Reference Engine is already configured to not process new "
                "requests, skipping this step"
            )
            return self._drain_state_machine()
        logging.info(
            "Stopping the Terraform Reference Engine from processing new requests"
        )
        for function_name, event_sources in self._get_event_source_data().items():
            result = result and self._update_event_source(
                function_name=function_name,
                event_sources=event_sources,
                event_source_enabled=False,
            )
        if not result:
            logging.error(
                "An error occurred while attempting to stop the Terraform Reference Engine from "
                "processing new requests, no further actions will be taken"
            )
            return False
        return result and self._drain_state_machine()

    def terminate_instances(
        self,
        suspend_asg_processes: bool = True,
    ) -> bool:
        """Terminates any running TRE execution instances and waits for them to complete.

        Args:
            suspend_asg_processes: If True, the auto scaling group which manages the TRE
                execution instances will have its `Launch` and `ReplaceUnhealthy` scaling
                operations suspended. Defaults to True.

        Returns:
            True if the TRE execution instances were successfully terminated, otherwise
            False.
        """
        instance_ids = self._get_instance_ids(check_health=True)
        if not instance_ids:
            logging.info(
                "No TRE execution instances are running, skipping the instance termination step"
            )
            return True
        logging.info(
            "Initiating a terminate operation for the following TRE execution "
            f"instances: {instance_ids}"
        )
        if suspend_asg_processes:
            self._suspend_asg_processes()
        try:
            response = self._ec2_client.terminate_instances(InstanceIds=instance_ids)
        except self._ec2_client.exceptions.ClientError as err:
            if err.response["Error"]["Code"] == "UnauthorizedOperation":
                logging.error(
                    f"The user '{self.user_identity}' is not authorized to terminate TRE "
                    f"execution instances '{instance_ids}'"
                )
                return False
            raise
        result = len(instance_ids) == len(response["TerminatingInstances"])
        logging.info(
            f"Successfully initiated termination for {len(instance_ids)} TRE execution instances"
        )
        return result and self._wait_for_instances(
            instance_ids=instance_ids, instance_state=[INSTANCE_STATE_TERMINATED]
        )

    @property
    def user_identity(self) -> str:
        """The ARN of the security principal under which we are executing."""
        if self._caller_identity is None:
            self._caller_identity = self._sts_client.get_caller_identity()
        return self._caller_identity["Arn"]

    def _drain_state_machine(
        self,
        timeout_seconds: int = 900,
    ) -> bool:
        """Waits for any in-flight TRE requests to complete before returning."""
        logging.info(
            "Waiting for any currently running Terraform Reference Engine executions to complete"
        )
        for state_machine_name in self.tre_state_machine_names:
            _timeout = self._get_timeout(timeout_seconds)
            _state_machine_arn = self._get_state_machine_arn(state_machine_name)
            while datetime.datetime.utcnow() < _timeout:
                execution_count = len(
                    self._sfn_client.list_executions(
                        stateMachineArn=_state_machine_arn,
                        statusFilter="RUNNING",
                    )["executions"]
                )
                if execution_count == 0:
                    return True
                logging.debug(
                    f"State machine '{state_machine_name}' has {execution_count} tasks actively running, "
                    f"rechecking in {self._check_interval_seconds}s"
                )
                time.sleep(self._check_interval_seconds)
        return False

    def _get_autoscaling_group_data(self) -> Optional[AutoScalingGroupTypeDef]:
        """Retrieves the configuration details of the TRE auto scaling group."""
        _autoscaling_group_data: Optional[AutoScalingGroupTypeDef] = None
        try:
            _autoscaling_group_data = self._asg_client.describe_auto_scaling_groups(
                AutoScalingGroupNames=[self.autoscaling_group_name]
            )["AutoScalingGroups"][0]
        except self._asg_client.exceptions.ClientError as err:
            if err.response["Error"]["Code"] == "AccessDenied":
                logging.error(
                    f"The user '{self.user_identity}' is not authorized to describe the TRE "
                    f"auto scaling group '{self.autoscaling_group_name}', no further actions "
                    "will be taken"
                )
                sys.exit(1)
            raise
        except IndexError:
            pass
        return _autoscaling_group_data

    def _get_event_source_data(
        self,
        force_refresh: bool = False,
    ) -> dict[str, list[EventSourceMappingConfigurationTypeDef]]:
        """Fetches the event sources configured for all TRE request handlers.

        Args:
            force_refresh: If True, the method will always execute an AWS
                API call to fetch the most current event source data,
                otherwise the cached data will be used.

        Warnings:
            If the underlying security principal is not authorized to execute the
            `lambda:ListEventSourceMappings` API action against any of the TRE
            request handlers, an error is logged and execution is halted with a
            non-zero exit code.
        """
        if self._event_source_data is not None and not force_refresh:
            return self._event_source_data
        self._event_source_data = {}
        for function_name in self.tre_handler_names:
            try:
                event_source_mappings = self._lambda_client.list_event_source_mappings(
                    FunctionName=function_name
                )["EventSourceMappings"]
                self._event_source_data[function_name] = [
                    x for x in event_source_mappings
                ]
            except self._lambda_client.exceptions.ClientError as err:
                if err.response["Error"]["Code"] == "AccessDeniedException":
                    logging.error(
                        f"The user '{self.user_identity}' is not authorized to describe the event "
                        f"sources for TRE function '{function_name}', no further actions will be taken"
                    )
                    sys.exit(1)
                raise
        return self._event_source_data

    def _get_event_sources(
        self,
        function_name: str,
        desired_state: Optional[str] = None,
        return_noncompliant_only: bool = False,
        force_refresh: bool = False,
    ) -> list[EventSourceMappingConfigurationTypeDef]:
        """Retrieves the configured event sources for the specified TRE Lambda function.

        Args:
            function_name: The name of the TRE Lambda function for which the configured
                event source mappings should be returned.

            desired_state: If defined, the method will check if the state of an event
                source matches the desired state when evaluating whether to include
                it in the returned data or not.

            return_noncompliant_only: If True, the method will only return event
                sources whose state does not match the value supplied via the
                `desired_state` argument. If no desired state value was supplied,
                this argument is ignored.

            force_refresh: If True, the method will always execute an AWS API
                call to retrieve the most recent event source data, otherwise the
                cached data will be used.

        Returns:
            A list of dicts mapping event source attribute names as keys to their
            corresponding configuration data. For example:

            >>> [{'UUID': '5ec315c4-26c8-4596-a588-09bc5aff0c81',
            >>>   'State': 'Enabled',
            >>>   'StateTransitionReason': 'USER_INITIATED',
            >>>   'FunctionResponseTypes': ['ReportBatchItemFailures']
            >>> }]

        """
        _event_sources: list[EventSourceMappingConfigurationTypeDef] = []
        try:
            for event_source in self._get_event_source_data(force_refresh)[
                function_name
            ]:
                if not desired_state:
                    _event_sources.append(event_source)
                    continue
                elif desired_state and return_noncompliant_only:
                    if not event_source["State"] == desired_state:
                        _event_sources.append(event_source)
                elif desired_state and not return_noncompliant_only:
                    if event_source["State"] == desired_state:
                        _event_sources.append(event_source)
        except KeyError:
            pass
        return _event_sources

    def _get_filters(
        self,
        instance_ids: Optional[list[str]] = None,
        instance_state: Optional[list[str]] = None,
    ) -> list[dict[str]]:
        """Returns a list of instance filters for the underlying TRE execution instances."""
        _filters: list[dict[str]] = [
            {"Name": "tag:Name", "Values": [self.instance_name]}
        ]
        if instance_ids is not None:
            _filters.append({"Name": "instance-id", "Values": instance_ids})
        if instance_state is not None:
            _filters.append({"Name": "instance-state-name", "Values": instance_state})
        return _filters

    def _get_instance_ids(
        self, check_health: bool = False, force_refresh: bool = True
    ) -> list[str]:
        """Returns the unique identifiers of the TRE execution instances.

        Args:
            check_health: If True, the method will only return IDs for TRE execution
                instances that are in-service and healthy members of the TRE auto
                scaling group.

            force_refresh: If True, the method will always execute an AWS API call
                to fetch the most recent instance status information from the TRE
                auto scaling group, otherwise the cached data will be used.

        Returns:
            A list of unique EC2 instance identifiers for the TRE execution instances.
        """
        _instance_ids: list[str] = []
        try:
            instances: list[InstanceTypeDef] = self.autoscaling_group_data(
                force_refresh
            )["Instances"]
            for instance in instances:
                if check_health and not instance["LifecycleState"] == "InService":
                    continue
                if check_health and not instance["HealthStatus"] == "Healthy":
                    continue
                _instance_ids.append(instance["InstanceId"])
        except KeyError:
            pass
        return _instance_ids

    def _get_service_client(
        self,
        aws_service: str = "ec2",
    ) -> Union[AutoScalingClient, EC2Client]:
        """Returns an initialized service client for the specified AWS service."""
        return boto3.client(aws_service, self.region)

    def _get_state_machine_arn(self, state_machine_name: str) -> Optional[str]:
        """Returns the ARN of the specified AWS Step Functions state machine."""
        _paginator = self._sfn_client.get_paginator("list_state_machines")
        _response = _paginator.paginate().build_full_result()["stateMachines"]
        for state_machine in _response:
            if state_machine["name"] == state_machine_name:
                return state_machine["stateMachineArn"]
        return None

    def _get_suspended_processes(self) -> list[str]:
        """Returns a list of suspended scaling processes from the TRE auto scaling group."""
        _suspended_processes = self.autoscaling_group_data(force_refresh=True)[
            "SuspendedProcesses"
        ]
        # noinspection PyTypeChecker
        return sorted(x["ProcessName"] for x in _suspended_processes)

    @staticmethod
    def _get_timeout(timeout_seconds: int = 900) -> datetime.datetime:
        """Calculates the UTC datetime that represents the given timeout threshold."""
        return datetime.datetime.utcnow() + datetime.timedelta(seconds=timeout_seconds)

    def _resume_asg_processes(
        self,
        scaling_processes: Optional[list[str]] = None,
    ) -> None:
        """Resumes the specified scaling processes for the TRE auto scaling group.

        If none of the specified scaling processes are suspended on the TRE auto
        scaling group, the method will take no action.

        Args:
            scaling_processes: An optional list of strings that represent the
                scaling processes that should be enabled on the TRE auto scaling
                group. If not specified, defaults to the `ReplaceUnhealthy` and
                `Launch` scaling processes.

        Warnings:
            If the underlying security principal is not authorized to execute the
            `autoscaling:ResumeProcesses` API action against the TRE auto scaling
            group, an error is logged and execution is halted with a non-zero exit
            code.
        """
        scaling_processes = scaling_processes or ["Launch", "ReplaceUnhealthy"]
        if not set(scaling_processes).intersection(self._get_suspended_processes()):
            logging.info(
                f"None of the specified scaling processes {scaling_processes} are "
                f"suspended for auto scaling group '{self.autoscaling_group_name}', "
                "skipping this step"
            )
            return None
        logging.info(
            "Resuming the following scaling processes for auto scaling group "
            f"'{self.autoscaling_group_name}': {scaling_processes}"
        )
        try:
            self._asg_client.resume_processes(
                AutoScalingGroupName=self.autoscaling_group_name,
                ScalingProcesses=scaling_processes,
            )
        except self._asg_client.exceptions.ClientError as err:
            if err.response["Error"]["Code"] == "AccessDenied":
                logging.error(
                    f"The user '{self.user_identity}' is not authorized to resume scaling "
                    f"operations for '{self.autoscaling_group_name}', no further actions "
                    "will be taken"
                )
                sys.exit(1)
            raise

    def _suspend_asg_processes(
        self,
        scaling_processes: Optional[list[str]] = None,
    ) -> None:
        """Suspends the specified scaling processes for the TRE auto scaling group.

        If the specified scaling processes are already suspended on the TRE auto
        scaling group, the method will take no action.

        Args:
            scaling_processes: An optional list of strings that represent the
                scaling processes that should be suspended on the TRE auto scaling
                group. If not specified, defaults to the `ReplaceUnhealthy` and
                `Launch` scaling processes.

        Warnings:
            If the underlying security principal is not authorized to execute the
            `autoscaling:SuspendProcesses` API action against the TRE auto scaling
            group, an error is logged and execution is halted with a non-zero exit
            code.
        """
        scaling_processes = scaling_processes or ["Launch", "ReplaceUnhealthy"]
        if set(scaling_processes).issubset(self._get_suspended_processes()):
            logging.info(
                f"The specified scaling processes {scaling_processes} are already "
                f"suspended for auto scaling group '{self.autoscaling_group_name}', "
                "skipping this step"
            )
            return None
        logging.info(
            "Suspending the following scaling processes for auto scaling group "
            f"'{self.autoscaling_group_name}': {scaling_processes}"
        )
        try:
            self._asg_client.suspend_processes(
                AutoScalingGroupName=self.autoscaling_group_name,
                ScalingProcesses=scaling_processes,
            )
        except self._asg_client.exceptions.ClientError as err:
            if err.response["Error"]["Code"] == "AccessDenied":
                logging.error(
                    f"The user '{self.user_identity}' is not authorized to suspend scaling "
                    f"operations for '{self.autoscaling_group_name}', no further actions "
                    "will be taken"
                )
                sys.exit(1)
            raise

    def _update_event_source(
        self,
        function_name: str,
        event_sources: list[EventSourceMappingConfigurationTypeDef],
        event_source_enabled: bool = True,
    ) -> bool:
        """Configures the supplied event sources for the specified TRE request handler.

        For a given TRE request handler, this method will either enable or disable the
        supplied event sources. When all event sources for a TRE request handler are
        disabled, that handler will no longer process new TRE requests.

        Args:
            function_name: The Lambda function name for the given TRE request handler.

            event_sources: A list of dicts that map event source attribute names as keys
                to their corresponding configuration data, as returned by the AWS Lambda
                ListEventSourceMappings API.

        Returns:
            True if all the supplied event sources for the specified TRE request handler
            were successfully updated to the desired state, otherwise False.

            If the underlying security principal is not authorized to execute the
            `lambda:UpdateEventSourceMappings` API action against any of the TRE
            request handlers, an error is logged the method immediately returns False.
        """
        _result: bool = False
        _desired_state = "Enabling" if event_source_enabled else "Disabling"
        for event_source in event_sources:
            event_source_uuid = event_source["UUID"]
            logging.info(
                f"{_desired_state} the event source '{event_source_uuid}' for TRE "
                f"function '{function_name}'"
            )
            try:
                self._lambda_client.update_event_source_mapping(
                    FunctionName=function_name,
                    UUID=event_source_uuid,
                    Enabled=event_source_enabled,
                )
            except self._lambda_client.exceptions.ClientError as err:
                if err.response["Error"]["Code"] == "AccessDeniedException":
                    logging.error(
                        f"The user '{self.user_identity}' is not authorized to update event source "
                        f"'{event_source_uuid}'"
                    )
                    return False
                raise
            _result = self._wait_for_event_source_state(
                event_source_uuid, event_source_enabled
            )
            if _result:
                _state = "enabled" if event_source_enabled else "disabled"
                logging.info(
                    f"The event source '{event_source_uuid}' for TRE function '{function_name}' "
                    f"has been successfully {_state}"
                )
        return _result

    def _wait_for_asg_instances(
        self,
        desired_instance_count: int,
        timeout_seconds: int = 900,
        strict_capacity: bool = False,
    ) -> bool:
        """Waits for the desired number of TRE execution instances to enter service.

        Args:
            desired_instance_count: The desired number of TRE execution instances that should
                be running and marked as healthy and in-service by the TRE auto scaling group.

            timeout_seconds: The number of seconds to wait for the TRE execution instances
                before timing out.

            strict_capacity: If True, the number of running TRE execution instances must exactly
                match the desired capacity. Otherwise, if *at least* the desired number of TRE
                execution instances are running, the method will signal success.

        Returns:
            True if the desired number of TRE execution instances are running and marked as
            healthy and in-service by the TRE auto scaling group, otherwise False.
        """
        _timeout = self._get_timeout(timeout_seconds)
        logging.info(
            "Waiting for the number of TRE execution instances in the auto scaling group "
            f"'{self.autoscaling_group_name}' to reach {desired_instance_count}"
        )
        while datetime.datetime.utcnow() < _timeout:
            asg_instance_ids = self._get_instance_ids(check_health=True)
            if not strict_capacity and desired_instance_count >= len(asg_instance_ids):
                logging.info(
                    "The number of TRE execution instances in the auto scaling group "
                    f"'{self.autoscaling_group_name}' is {desired_instance_count}"
                )
                return True
            if desired_instance_count == len(asg_instance_ids):
                logging.info(
                    "The number of TRE execution instances in the auto scaling group "
                    f"'{self.autoscaling_group_name}' is {desired_instance_count}"
                )
                return True
            logging.debug(
                f"The number of TRE execution instances in the auto scaling group "
                f"'{self.autoscaling_group_name}' has not reached {desired_instance_count}, "
                f"rechecking in {self._check_interval_seconds}s"
            )
            time.sleep(self._check_interval_seconds)
        return False

    def _wait_for_event_source_state(
        self,
        event_source_uuid: str,
        event_source_enabled: bool = True,
        timeout_seconds: int = 900,
    ) -> bool:
        """Waits for the specified TRE request handler event source to reach the desired state.

        Args:
            event_source_uuid: The UUID of the event source mapping that should be monitored.

            event_source_enabled: If True, the event source mapping should be enabled, otherwise
                it should be disabled.

            timeout_seconds: The number of seconds to wait for the event source to reach the
                desired state before timing out.

        Returns:
            True if the event source reached the desired state, otherwise False.
        """
        _timeout = self._get_timeout(timeout_seconds)
        _check_interval: int = 5
        _desired_state = "Enabled" if event_source_enabled else "Disabled"
        logging.info(
            f"Waiting for event source '{event_source_uuid}' to reach the desired "
            f"state '{_desired_state}'"
        )
        while datetime.datetime.utcnow() < _timeout:
            try:
                _response = self._lambda_client.get_event_source_mapping(
                    UUID=event_source_uuid
                )
            except self._lambda_client.exceptions.ClientError as err:
                if err.response["Error"]["Code"] == "AccessDeniedException":
                    logging.error(
                        f"The user '{self.user_identity}' is not authorized to describe the "
                        f"event source '{event_source_uuid}'"
                    )
                    return False
                raise
            if _response["State"] == _desired_state:
                return True
            logging.debug(
                f"Event source '{event_source_uuid}' has not yet reached the desired state "
                f"'{_desired_state}', rechecking in {_check_interval}s"
            )
            time.sleep(_check_interval)
        return False

    def _wait_for_instances(
        self,
        desired_instance_count: Optional[int] = None,
        instance_ids: Optional[list[str]] = None,
        instance_state: Optional[list[str]] = None,
        timeout_seconds: int = 900,
    ) -> bool:
        """Waits for the desired number of TRE execution instances to enter the desired state(s).

        This method will wait for the specified TRE execution instances to enter one of the specified
        desired EC2 states, without regard for their status in the TRE auto scaling group. This method
        is used to verify both TRE execution instance initialization and termination.

        Args:
            desired_instance_count: The desired number of TRE execution instances that should enter
                one of the specified desired states. If not specified, this will be set to the number
                of instance IDs if any were supplied, or will fall back to the desired capacity set
                on the TRE auto scaling group.

            instance_ids: An optional list of unique EC2 instance identifiers for TRE execution
                instances that should be monitored.

            instance_state: An optional list of EC2 instance states which the TRE execution instances
                should be monitored against. If an instance enters *any* of the EC2 states defined in
                this list, it will be considered successful.

                If not specified, the TRE execution instances will be monitored for entering the
                `running` state.

            timeout_seconds: The number of seconds to wait for the TRE execution instances
                before timing out.

        Returns:
            True if the desired number of TRE execution instances have reached one or more of the
            desired EC2 states, otherwise False.
        """
        result: bool = False
        instance_state = instance_state or [INSTANCE_STATE_RUNNING]
        if desired_instance_count is None:
            if instance_ids:
                desired_instance_count = len(instance_ids)
            else:
                desired_instance_count = (
                    self.autoscaling_group_data()["DesiredCapacity"]
                    or DEFAULT_ASG_DESIRED_CAPACITY
                )
        _filters = self._get_filters(instance_ids, instance_state)
        _timeout = self._get_timeout(timeout_seconds)
        _paginator = self._ec2_client.get_paginator("describe_instances")
        logging.info(
            f"Waiting for TRE execution instances to reach one of the following "
            f"desired states: {instance_state}"
        )
        while datetime.datetime.utcnow() < _timeout:
            try:
                _response = _paginator.paginate(Filters=_filters).build_full_result()[
                    "Reservations"
                ]
            except self._ec2_client.exceptions.ClientError as err:
                if err.response["Error"]["Code"] == "UnauthorizedOperation":
                    logging.error(
                        f"The user '{self.user_identity}' is not authorized to describe TRE "
                        f"execution instances '{instance_ids}'"
                    )
                    return False
                raise
            if not _response and not desired_instance_count == 0:
                logging.debug(
                    "The required number of TRE execution instances have not reached "
                    f"a desired state, rechecking in {self._check_interval_seconds}s"
                )
                time.sleep(self._check_interval_seconds)
                continue
            if not _response and desired_instance_count == 0:
                result = True
                break
            _instances = _response[0]["Instances"]
            if len(_instances) >= desired_instance_count:
                result = True
                break
            logging.debug(
                "The required number of TRE execution instances have not reached "
                f"a desired state, rechecking in {self._check_interval_seconds}s"
            )
            time.sleep(self._check_interval_seconds)
        logging.info(
            "All TRE execution instances have reached one of the desired states"
        )
        desired_instance_count = (
            0
            if not instance_state == [INSTANCE_STATE_RUNNING]
            else desired_instance_count
        )
        return result and self._wait_for_asg_instances(
            desired_instance_count,
            timeout_seconds,
            strict_capacity=True,
        )


def log_execution_time(
    execution_start_time: float,
    exit_code: Optional[int] = None,
) -> None:
    logging.info(
        f"Total execution time: {math.floor(time.time() - execution_start_time)}s"
    )
    if exit_code is not None:
        sys.exit(exit_code)


def main() -> None:
    start_time = time.time()
    args = __parse_arguments()
    region: Optional[str] = __get_aws_region(args)

    if not region:
        raise ValueError(
            "You must specify an AWS region using the `--region` argument or by setting "
            f"one of the following environment variables: {AWS_REGION_ENV_VARS}"
        )

    tre = TerraformReferenceEngine(
        autoscaling_group_name=args.autoscaling_group_name,
        instance_name=args.instance_name,
        region=__get_aws_region(args),
    )

    if args.verbose > 0:
        logging.debug(
            f"Executing 'manage-terraform-engine.py' with the following arguments: \n{args.__dict__}"
        )
        logging.debug(
            f"Executing as the following security principal: '{tre.user_identity}'"
        )

    if args.action == ACTION_STATUS:
        if not tre.check_status():
            logging.warning("Terraform Reference Engine Status: 'Disabled'")
        else:
            logging.info("Terraform Reference Engine Status: 'Enabled'")
        log_execution_time(execution_start_time=start_time, exit_code=0)

    if args.action == ACTION_STOP:
        _prompt_message = (
            "You have requested to change the status of the Terraform Reference Engine in "
            f"AWS account '{tre.account_id}' and region '{tre.region}' to 'Disabled'"
        )

        if not tre.check_status():
            logging.info("Terraform Reference Engine Status: 'Disabled'")
            logging.info(
                "The Terraform Reference Engine is already in the 'Disabled' state, any new "
                "requests will remain in their SQS queues until restarted or they timeout"
            )
            log_execution_time(execution_start_time=start_time, exit_code=0)
        logging.info("Terraform Reference Engine Status: 'Enabled'")

        if not args.auto_approve and not __request_approval(_prompt_message):
            log_execution_time(execution_start_time=start_time, exit_code=1)

        if not tre.stop_request_processing():
            log_execution_time(execution_start_time=start_time, exit_code=1)

        if not tre.terminate_instances():
            logging.error(
                "An error occurred while attempting to terminate the Terraform Reference "
                "Engine execution instances, no further action will be taken"
            )
            log_execution_time(execution_start_time=start_time, exit_code=1)

        if not tre.check_status():
            logging.info("Terraform Reference Engine Status: 'Disabled'")
            logging.info(
                "The Terraform Reference Engine has been successfully stopped, any new requests "
                "will remain in their SQS queues until restarted or they timeout"
            )
            log_execution_time(execution_start_time=start_time, exit_code=0)
        else:
            logging.error("Terraform Reference Engine Status: 'Enabled'")
            logging.error(
                "An error occurred while attempting to stop the Terraform Reference Engine"
            )
            log_execution_time(execution_start_time=start_time, exit_code=1)

    if args.action == ACTION_START:
        _prompt_message = (
            "You have requested to change the status of the Terraform Reference Engine in "
            f"AWS account '{tre.account_id}' and region '{tre.region}' to 'Enabled'"
        )

        if tre.check_status():
            logging.info("Terraform Reference Engine Status: 'Enabled'")
            logging.info(
                "The Terraform Reference Engine status is already 'Enabled', any new requests "
                "received or requests currently in the TRE SQS queues will be processed"
            )
            log_execution_time(execution_start_time=start_time, exit_code=0)
        logging.info("Terraform Reference Engine Status: 'Disabled'")

        if not args.auto_approve and not __request_approval(_prompt_message):
            log_execution_time(execution_start_time=start_time, exit_code=1)

        if not tre.start_instances():
            logging.error(
                "An error occurred while attempting to start the Terraform Reference Engine "
                "execution instances, no further actions will be taken"
            )
            log_execution_time(execution_start_time=start_time, exit_code=1)

        if not tre.resume_request_processing():
            logging.error(
                "An error occurred while attempting to resume the Terraform Reference Engine "
                "request processing, no further actions will be taken"
            )
            log_execution_time(execution_start_time=start_time, exit_code=1)

        if tre.check_status():
            logging.info("Terraform Reference Engine Status: 'Enabled'")
            logging.info(
                "The Terraform Reference Engine has been successfully started, any new requests "
                "received or requests currently in the TRE SQS queues will be processed"
            )
            log_execution_time(execution_start_time=start_time, exit_code=0)
        else:
            logging.error("Terraform Reference Engine Status: 'Disabled'")
            logging.error(
                "An error occurred while attempting to start the Terraform Reference Engine"
            )
            log_execution_time(execution_start_time=start_time, exit_code=1)

    if args.action == ACTION_REPLACE:
        _prompt_message = (
            "You have requested to temporarily change the status of the Terraform Reference Engine "
            f"in AWS account '{tre.account_id}' and region '{tre.region}' to 'Disabled', replace the "
            f"TRE execution instances, and then resume the Terraform Reference Engine"
        )

        if not args.auto_approve and not __request_approval(_prompt_message):
            log_execution_time(execution_start_time=start_time, exit_code=1)

        if tre.check_status():
            logging.info("Terraform Reference Engine Status: 'Enabled'")
            if not tre.stop_request_processing():
                log_execution_time(execution_start_time=start_time, exit_code=1)

            if not tre.terminate_instances(suspend_asg_processes=False):
                logging.error(
                    "An error occurred while attempting to terminate the Terraform Reference "
                    "Engine execution instances, no further action will be taken"
                )
                log_execution_time(execution_start_time=start_time, exit_code=1)

        logging.info("Terraform Reference Engine Status: 'Disabled'")
        if not tre.start_instances():
            logging.error(
                "An error occurred while attempting to start the Terraform Reference Engine "
                "execution instances, no further actions will be taken"
            )
            log_execution_time(execution_start_time=start_time, exit_code=1)

        if not tre.resume_request_processing():
            log_execution_time(execution_start_time=start_time, exit_code=1)

        if tre.check_status():
            logging.info("Terraform Reference Engine Status: 'Enabled'")
            logging.info(
                "The Terraform Reference Engine has been successfully started and the TRE "
                "execution instances have been replaced, any new requests received or "
                "\n requests currently in the TRE SQS queues will be processed"
            )
            log_execution_time(execution_start_time=start_time, exit_code=0)
        else:
            logging.error("Terraform Reference Engine Status: 'Disabled'")
            logging.error(
                "An error occurred while attempting to start the Terraform Reference Engine and "
                "replace the TRE execution instances"
            )
            log_execution_time(execution_start_time=start_time, exit_code=1)


if __name__ == "__main__":
    main()

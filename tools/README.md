# Terraform Reference Engine Tools

This folder contains various command line tools and libraries to help you easily deploy and manage the Terraform 
Reference Engine (TRE) in your AWS environment.

- 🚀 [**deploy-terraform-engine.sh**](deploy-terraform-engine.sh) enables you to easily deploy the Terraform Reference 
  Engine (TRE) in your AWS environment or safely update a previously deployed TRE environment.  
- 🔎 [**manage-terraform-engine.py**](manage-terraform-engine.py) enables you to safely and easily manage the status of 
  the Terraform Reference Engine deployed in your AWS environment: pause or resume request processing, quiesce all 
  actively executing requests, and terminate or replace execution instances.
---

## Prerequisites

The Terraform Reference Engine tools can be used from any Linux or macOS environment with the following pre-requisites 
installed:
   - 📦 Docker: [_Docker Desktop for Mac_](https://docs.docker.com/desktop/install/mac-install/), [_Docker Engine for Linux_](https://docs.docker.com/engine/install/)
   - 🐍 Python 3: [_Python 3 Releases for macOS_](https://www.python.org/downloads/macos/), [_Python 3 Releases for Linux_](https://www.python.org/downloads/source/)
   - ☁️ AWS CLI: [_Install or Update the AWS CLI_](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)

> [!NOTE]
> _You must also ensure your environment is [properly configured with valid AWS credentials](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html#configuring-credentials)
> and a region is set for the AWS environment where the Terraform Reference Engine is or will be deployed._

The tools in this folder automatically check for the mandatory prerequisites. You can check that your local environment 
meets all prerequisites at any time by running the `make check-prerequisites` convenience target in the project 
[Makefile](../Makefile) (_execute form the [project root directory](../.)_):

```shell
❯ make check-prerequisites
[ERROR] Docker is required but the daemon is not running, please start it and try again.
make: *** [check-docker] Error 1

❯ make check-prerequisites         
All prerequisites are installed and configured properly.
```
---

## Terraform Reference Engine Deployment

The [**deploy-terraform-engine.sh**](deploy-terraform-engine.sh) script provides a robust tool that can help you 
easily and safely deploy the Terraform Reference Engine in your AWS environment.

- 🐍 Automatically configures a Python virtual environment, installs and upgrades all required packages, and 
  ensure the virtual environment is activated.
- ☁️ Dynamically determines the AWS account and region in which it is operating.
- 🚧 Checks if the Terraform Reference Engine bootstrap resources have been deployed in the AWS environment
  and automatically deploys them through a CloudFormation Stack if not.
- 📦 Builds the Terraform Reference Engine packages and deploys artifacts to S3 for staging.
- 🦺 Automatically determines if the Terraform Reference Engine has been previously deployed in the target 
  AWS environment, and if so, gracefully stops the Terraform Reference Engine.  
- 🚧 Deploys the Terraform Reference Engine in the AWS environment.
- 🦺 If updating a previous deployment of the Terraform Reference Engine, the script will automatically 
  re-enable the Terraform Reference Engine and resume request processing.

<br />
<details>
  <summary><b>Usage Information</b></summary>
  
  Provided below are the supported options and flags that can be passed to `deploy-terraform-engine.sh` to customize 
  its default behavior. The most current usage information can always be obtained by executing 
  `deploy-terraform-engine.sh --help`.

  ```shell
  Deploys the Terraform Reference Engine (TRE) to an AWS environment.

  Usage:
    deploy-terraform-engine.sh [--region <region>]

  Options:
    --region <region>
      The AWS region where the TRE should be deployed.
      If unspecified, the script attempts to use values set in either the
      AWS_DEFAULT_REGION or AWS_REGION environment variables.

    --bootstrap-stack-name <bootstrap_stack_name>
      The name assigned to the bootstrap TRE CloudFormation stack.
      Defaults to 'Bootstrap-TRE'.

    --bootstrap-template <bootstrap_template>
      The CloudFormation template file used to create bootstrap resources.
      Defaults to '(PROJECT_ROOT_DIR)/cfn-templates/Bootstrap.yaml'.

    --stack-name <main_stack_name>
      The name assigned to the main TRE CloudFormation stack.
      Defaults to 'SAM-TRE'.

    --stack-template <stack_template>
      The CloudFormation template file used to create TRE resources.
      Defaults to '(PROJECT_ROOT_DIR)/template.yaml'.

    --version
      Shows the version of this tool.

    -h, --help
      Shows this help message.
  ```
</details>

### Deploy or Update the Terraform Reference Engine

To deploy the Terraform Reference Engine in your AWS environment, or to update an existing deployment, execute the 
following command, replacing `<AWS_REGION>` with the correct region for your AWS environment:
```shell
❯ ./deploy-terraform-engine.sh --region <AWS_REGION>
```
> [!NOTE]
> _If you do not pass the `--region` option, the script will attempt to automatically determine the correct region by
> checking the `AWS_REGION`, `AWS_PROFILE_REGION`, and `AWS_DEFAULT_REGION` environment variables (in order of
> precedence) and fail if the region cannot be determined._
---

## Terraform Reference Engine Control

The [**manage-terraform-engine.py**](manage-terraform-engine.py) script provides a robust tool that can help you 
safely and easily manage the status of the Terraform Reference Engine deployed in your AWS environment. With this tool,
you can pause or resume request processing, wait for any actively executing requests to complete, and terminate or 
replace execution instances.

<br />
<details>
  <summary><b>Usage Information</b></summary>
  
  Provided below are the supported options and flags that can be passed to `manage-terraform-engine.py` to customize 
  its default behavior. The most current usage information can always be obtained by executing 
  `manage-terraform-engine.py --help`.

  ```shell
  usage: manage-terraform-engine.py [-h] [-a {start,status,stop,replace}] [-r REGION] [--auto-approve] [--instance-name INSTANCE_NAME] [--autoscaling-group-name AUTOSCALING_GROUP_NAME] [-v]

  options:
    -h, --help            show this help message and exit
    -a {start,status,stop,replace}, --action {start,status,stop,replace}
                          (Optional) The action to perform against the Terraform Reference Engine. Defaults to 'status'.
    -r REGION, --region REGION
                          (Optional) The region where the Terraform Reference Engine environment is deployed. Defaults to 'None'.
    --auto-approve        
                          (Optional) Do not require interactive approval for changes. Defaults to 'False'.
    --instance-name INSTANCE_NAME
                          (Optional) The name assigned to the Terraform Reference Engine execution instances. Defaults to 'TerraformEngineExecutionInstance'.
    --autoscaling-group-name AUTOSCALING_GROUP_NAME 
                          (Optional) The name assigned to the Terraform Reference Engine auto scaling group. Defaults to 'TerraformAutoscalingGroup'.
    -v, --verbose         
                          (Optional) Increase the verbosity of the log output.
  ```
</details>

### Check Status of Terraform Reference Engine

To check the current status of the Terraform Reference Engine in the target AWS environment, execute the following 
command, replacing `<AWS_REGION>` with the correct region for your AWS environment:
```shell
❯ ./manage-terraform-engine.py \
    --region <AWS_REGION> \
    --action status
2023-08-16T13:53:48Z [INFO] - Checking the status of the Terraform Reference Engine in AWS account '123456789012' and region 'us-east-2'
2023-08-16T13:53:49Z [INFO] - Terraform Reference Engine Status: 'Enabled'
2023-08-16T13:53:49Z [INFO] - Total execution time: 3s
```
> [!NOTE]
> _If you do not pass the `--region` option, the script will attempt to automatically determine the correct region by
> checking the `AWS_REGION`, `AWS_PROFILE_REGION`, and `AWS_DEFAULT_REGION` environment variables (in order of
> precedence) and fail if the region cannot be determined._

The `status` command classifies the Terraform Reference Engine in the target AWS environment as `Enabled` if all the 
following conditions are true:
- ✅ The number of running and healthy TRE execution instances matches the desired instance count defined by the TRE 
  auto scaling group.
- ✅ The TRE auto scaling group has no suspended scaling processes.
- ✅ All event source mappings that invoke TRE functions to process requests from the TRE queues are enabled.  

### Safely Pause the Terraform Reference Engine

To safely pause the processing of requests by the Terraform Reference Engine in the target AWS environment and 
terminate TRE execution instances, execute the following command, replacing `<AWS_REGION>` with the correct region 
for your AWS environment:
```shell
❯ ./manage-terraform-engine.py \
    --region <AWS_REGION> \
    --action stop  
2023-08-16T14:07:44Z [INFO] - Checking the status of the Terraform Reference Engine in AWS account '123456789012' and region 'us-east-2'
2023-08-16T14:07:45Z [INFO] - Terraform Reference Engine Status: 'Enabled'
2023-08-16T14:07:45Z [WARNING] - You have requested to change the status of the Terraform Reference Engine in AWS account '123456789012' and region 'us-east-2' to 'Disabled'
Do you want to continue? [Y/n]: Y
2023-08-16T14:07:54Z [INFO] - Stopping the Terraform Reference Engine from processing new requests
2023-08-16T14:07:54Z [INFO] - Disabling the event source '6482f2da-c32c-406b-b603-b0263a8404bb' for TRE function 'TerraformEngineProvisioningHandlerLambda'
2023-08-16T14:07:54Z [INFO] - Waiting for event source '6482f2da-c32c-406b-b603-b0263a8404bb' to reach the desired state 'Disabled'
2023-08-16T14:08:00Z [INFO] - The event source '6482f2da-c32c-406b-b603-b0263a8404bb' for TRE function 'TerraformEngineProvisioningHandlerLambda' has been successfully disabled
2023-08-16T14:08:00Z [INFO] - Disabling the event source '8c9af8db-d170-4d1c-aba8-5b27081eb08f' for TRE function 'TerraformEngineProvisioningHandlerLambda'
2023-08-16T14:08:00Z [INFO] - Waiting for event source '8c9af8db-d170-4d1c-aba8-5b27081eb08f' to reach the desired state 'Disabled'
2023-08-16T14:08:16Z [INFO] - The event source '8c9af8db-d170-4d1c-aba8-5b27081eb08f' for TRE function 'TerraformEngineProvisioningHandlerLambda' has been successfully disabled
2023-08-16T14:08:16Z [INFO] - Disabling the event source '58e4cae3-a00c-416b-a809-f101372c110e' for TRE function 'TerraformEngineTerminateHandlerLambda'
2023-08-16T14:08:16Z [INFO] - Waiting for event source '58e4cae3-a00c-416b-a809-f101372c110e' to reach the desired state 'Disabled'
2023-08-16T14:08:32Z [INFO] - The event source '58e4cae3-a00c-416b-a809-f101372c110e' for TRE function 'TerraformEngineTerminateHandlerLambda' has been successfully disabled
2023-08-16T14:08:32Z [INFO] - Waiting for any currently running Terraform Reference Engine executions to complete
2023-08-16T14:08:33Z [INFO] - Initiating a terminate operation for the following TRE execution instances: ['i-0612b06d5f9fb17d0']
2023-08-16T14:08:33Z [INFO] - Suspending the following scaling processes for auto scaling group 'TerraformAutoscalingGroup': ['Launch', 'ReplaceUnhealthy']
2023-08-16T14:08:34Z [INFO] - Successfully initiated termination for 1 TRE execution instances
2023-08-16T14:08:34Z [INFO] - Waiting for TRE execution instances to reach one of the following desired states: ['terminated']
2023-08-16T14:09:04Z [INFO] - All TRE execution instances have reached one of the desired states
2023-08-16T14:09:04Z [INFO] - Waiting for the number of TRE execution instances in the auto scaling group 'TerraformAutoscalingGroup' to reach 0
2023-08-16T14:10:22Z [INFO] - Checking the status of the Terraform Reference Engine in AWS account '123456789012' and region 'us-east-2'
2023-08-16T14:10:22Z [INFO] - Terraform Reference Engine Status: 'Disabled'
2023-08-16T14:10:22Z [INFO] - The Terraform Reference Engine has been successfully stopped, any new requests will remain in their SQS queues until restarted or they timeout
2023-08-16T14:10:22Z [INFO] - Total execution time: 159s
```
> [!NOTE]
> _By default, commands that make changes to the Terraform Reference Engine require interactive approval before 
> continuing. If you prefer the commands do not require interactive approval, you can pass the `--auto-approve` flag._

> [!NOTE]
> _If you do not pass the `--region` option, the script will attempt to automatically determine the correct region by
> checking the `AWS_REGION`, `AWS_PROFILE_REGION`, and `AWS_DEFAULT_REGION` environment variables (in order of
> precedence) and fail if the region cannot be determined._

The `stop` command takes the following actions against the Terraform Reference Engine in the target AWS environment:
- 🔎 Automatically determines the current status of the Terraform Reference Engine in the target AWS environment. If
  the current status is `Disabled`, the command reports this and exits.
- 🦺 If the current status is `Enabled`, the tool requests interactive approval from the user before taking steps to 
  stop the Terraform Reference Engine, unless the `--auto-approve` flag was passed. If the user fails to provide 
  approval after 3 prompts, the command halts with an error.
- ⏱️ Pauses processing of new TRE requests by disabling the event source mappings for all TRE functions.
  > [!NOTE]
  > _Any new TRE requests will remain in their SQS queues until request processing is resumed, or they time out._
- ⌛️ The command enters a block state, waiting for any TRE requests that are actively executing to finish. _The time 
  required to complete this step could be significant if any long-running Terraform operations are in-flight._
- 💥 Terminates all TRE execution instances that are in a `running` or `stopped` state, and suspends the `Launch` and 
  `ReplaceUnhealthy` scaling processes for the TRE auto scaling group to prevent new instance launches.

### Safely Resume the Terraform Reference Engine

To safely resume the processing of requests by the Terraform Reference Engine in the target AWS environment and 
launch new TRE execution instances, execute the following command, replacing `<AWS_REGION>` with the correct region 
for your AWS environment:
```shell
❯ ./manage-terraform-engine.py \
    --region <AWS_REGION> \
    --action start
2023-08-16T14:38:38Z [INFO] - Checking the status of the Terraform Reference Engine in AWS account '123456789012' and region 'us-east-2'
2023-08-16T14:38:38Z [INFO] - Terraform Reference Engine Status: 'Disabled'
2023-08-16T14:38:38Z [WARNING] - You have requested to change the status of the Terraform Reference Engine in AWS account '123456789012' and region 'us-east-2' to 'Enabled'
Do you want to continue? [Y/n]: Y
2023-08-16T14:38:38Z [INFO] - Starting Terraform Reference Engine execution instances
2023-08-16T14:38:38Z [INFO] - Resuming the following scaling processes for auto scaling group 'TerraformAutoscalingGroup': ['Launch', 'ReplaceUnhealthy']
2023-08-16T14:38:38Z [INFO] - Waiting for TRE execution instances to reach one of the following desired states: ['running']
2023-08-16T14:39:24Z [INFO] - All TRE execution instances have reached one of the desired states
2023-08-16T14:39:24Z [INFO] - Waiting for the number of TRE execution instances in the auto scaling group 'TerraformAutoscalingGroup' to reach 1
2023-08-16T14:39:55Z [INFO] - The number of TRE execution instances in the auto scaling group 'TerraformAutoscalingGroup' is 1
2023-08-16T14:39:56Z [INFO] - Resuming the processing of new requests by the Terraform Reference Engine
2023-08-16T14:39:56Z [INFO] - Enabling the event source '6482f2da-c32c-406b-b603-b0263a8404bb' for TRE function 'TerraformEngineProvisioningHandlerLambda'
2023-08-16T14:39:56Z [INFO] - Waiting for event source '6482f2da-c32c-406b-b603-b0263a8404bb' to reach the desired state 'Enabled'
2023-08-16T14:40:06Z [INFO] - The event source '6482f2da-c32c-406b-b603-b0263a8404bb' for TRE function 'TerraformEngineProvisioningHandlerLambda' has been successfully enabled
2023-08-16T14:40:06Z [INFO] - Enabling the event source '8c9af8db-d170-4d1c-aba8-5b27081eb08f' for TRE function 'TerraformEngineProvisioningHandlerLambda'
2023-08-16T14:40:07Z [INFO] - Waiting for event source '8c9af8db-d170-4d1c-aba8-5b27081eb08f' to reach the desired state 'Enabled'
2023-08-16T14:40:17Z [INFO] - The event source '8c9af8db-d170-4d1c-aba8-5b27081eb08f' for TRE function 'TerraformEngineProvisioningHandlerLambda' has been successfully enabled
2023-08-16T14:40:17Z [INFO] - Enabling the event source '58e4cae3-a00c-416b-a809-f101372c110e' for TRE function 'TerraformEngineTerminateHandlerLambda'
2023-08-16T14:40:18Z [INFO] - Waiting for event source '58e4cae3-a00c-416b-a809-f101372c110e' to reach the desired state 'Enabled'
2023-08-16T14:40:38Z [INFO] - The event source '58e4cae3-a00c-416b-a809-f101372c110e' for TRE function 'TerraformEngineTerminateHandlerLambda' has been successfully enabled
2023-08-16T14:40:38Z [INFO] - Checking the status of the Terraform Reference Engine in AWS account '123456789012' and region 'us-east-2'
2023-08-16T14:40:40Z [INFO] - Terraform Reference Engine Status: 'Enabled'
2023-08-16T14:40:40Z [INFO] - The Terraform Reference Engine has been successfully started, any new requests received or requests currently in the TRE SQS queues will be processed
2023-08-16T14:40:40Z [INFO] - Total execution time: 123s
```
> [!NOTE]
> _By default, commands that make changes to the Terraform Reference Engine require interactive approval before 
> continuing. If you prefer the commands do not require interactive approval, you can pass the `--auto-approve` flag._

> [!NOTE]
> _If you do not pass the `--region` option, the script will attempt to automatically determine the correct region by
> checking the `AWS_REGION`, `AWS_PROFILE_REGION`, and `AWS_DEFAULT_REGION` environment variables (in order of
> precedence) and fail if the region cannot be determined._

The `start` command takes the following actions against the Terraform Reference Engine in the target AWS environment:
- 🔎 Automatically determines the current status of the Terraform Reference Engine in the target AWS environment. If
  the current status is `Enabled`, the command reports this and exits.
- 🦺 If the current status is `Disabled`, the tool requests interactive approval from the user before taking steps to 
  start the Terraform Reference Engine, unless the `--auto-approve` flag was passed. If the user fails to provide 
  approval after 3 prompts, the command halts with an error.
- 🚀 Resumes the `Launch` and `ReplaceUnhealthy` suspended scaling processes for the TRE auto scaling group, and waits 
  for the number of running and healthy TRE execution instances to match the desired instance count. 
- ⏱️ Resumes  processing of new TRE requests by enabling the event source mappings for all TRE functions.
  > [!NOTE]
  > _Any new TRE requests or those already in the SQS queues will be processed._


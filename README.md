# AWS Service Catalog Reference Engine for Terraform Open Source

The Terraform Reference Engine (TRE) project provides a reference solution you can use to deploy a [Terraform open 
source](https://developer.hashicorp.com/terraform/intro/terraform-editions#terraform-open-source) provisioning engine 
in your AWS Service Catalog central administration account (e.g., hub account). With the Terraform Reference Engine 
deployed, you can now use AWS Service Catalog to organize and enable self-service provisioning with governance for 
your Terraform configurations within AWS at scale.

You only need to deploy the Terraform Reference Engine once, in your AWS Service Catalog hub account, and the setup 
takes just a few minutes using the [automated deployment tools](tools/deploy-terraform-engine.sh) provided in this 
project.

For more information about Terraform Open Source and AWS Service Catalog, see the [Getting Started with Terraform Open Source](https://docs.aws.amazon.com/servicecatalog/latest/adminguide/getstarted-Terraform.html)
section of the AWS Service Catalog Administrator Guide.

---

## Installation Prerequisites

The Terraform Reference Engine can be installed from any Linux or macOS environment with the following pre-requisites 
installed:
   - 📦 Docker: [_Docker Desktop for Mac_](https://docs.docker.com/desktop/install/mac-install/), [_Docker Engine for Linux_](https://docs.docker.com/engine/install/)
   - 🐍 Python 3: [_Python 3 Releases for macOS_](https://www.python.org/downloads/macos/), [_Python 3 Releases for Linux_](https://www.python.org/downloads/source/)
   - ☁️ AWS CLI: [_Install or Update the AWS CLI_](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)

> [!NOTE]
> _You must also ensure your environment is [properly configured with valid AWS credentials](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html#configuring-credentials)
> and a region is set for the AWS environment where the Terraform Reference Engine is or will be deployed._

_The tools in this project automatically check for the mandatory prerequisites. You can check that your local  
environment meets all prerequisites at any time by running `make check-prerequisites` from the 
[project root directory](.):_
```shell
❯ make check-prerequisites
[ERROR] Docker is required but the daemon is not running, please start it and try again.
make: *** [check-docker] Error 1

❯ make check-prerequisites         
All prerequisites are installed and configured properly.
```
---

## Automated Installation

This project includes [tools](tools) that will help you easily deploy and manage the Terraform Reference Engine (TRE) 
in your AWS environment:
   - 🚀 [**deploy-terraform-engine.sh**](tools/deploy-terraform-engine.sh): enables you to easily deploy the Terraform 
     Reference Engine (TRE) in your AWS environment or safely update a previously deployed TRE environment. 
   - 🔎 [**manage-terraform-engine.py**](tools/manage-terraform-engine.py): enables you to safely and easily manage the 
     status of the Terraform Reference Engine deployed in your AWS environment: pause or resume request processing, 
     quiesce all actively executing requests, and terminate or replace execution instances.

To deploy the Terraform Reference Engine in your AWS environment, or to update an existing deployment, execute the 
following command, replacing `<AWS_REGION>` with the correct region for your AWS environment:
```shell
❯ ./tools/deploy-terraform-engine.sh --region <AWS_REGION>
```
> [!NOTE]
> _If you do not pass the `--region` option, the script will attempt to automatically determine the correct region by
> checking the `AWS_REGION`, `AWS_PROFILE_REGION`, and `AWS_DEFAULT_REGION` environment variables (in order of
> precedence) and fail if the region cannot be determined._

> [!NOTE]
> _The [**deploy-terraform-engine.sh**](tools/deploy-terraform-engine.sh) tool automatically detects when it is run in
> an AWS environment with a previously Terraform Reference Engine deployment, and will safely pause the Terraform 
> Reference Engine before proceeding. See the [tool documentation](tools/README.md) for additional detail._
---

## Manual Installation

If you prefer to install the Terraform Reference Engine manually, you may perform the following steps. Please note, 
unless otherwise specified, all commands should be executed from the [project root directory](.).

> [!NOTE]
> _To proceed with the manual installation steps, please ensure your local environment meets [all prerequisite](#installation-prerequisites)
> requirements._

<details>
  <summary><b>Manual Installation Steps</b></summary>

  ### Setup Your Environment
In this step, you will ensure your local environment passes all prerequisite checks and that you have a Python virtual 
environment that is properly configured for Terraform Reference Engine development.

1. Ensure an AWS region is set in your environment by executing the following command, replacing
   `<AWS_REGION>` with the correct region for your AWS environment:
   ```shell
   ❯ export AWS_REGION=<AWS_REGION>
   ```
2. Ensure an AWS account ID is set in your environment by executing the following command:
   ```shell
   ❯ export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --output text --query Account 2>&1 | egrep "^[0-9]{12}$")
   ❯ [[ -z "${AWS_ACCOUNT_ID}" ]] && echo "[ERROR] Unable to determine the ID of your AWS account, please ensure your `
       `AWS credentials are valid and your profile is configured properly."
   ```
3. Verify your local environment passes all prerequisite checks by executing the following command:
   ```shell
   ❯ make check-prerequisites
   All prerequisites are installed and configured properly.
   ```
4. Create a new Python virtual environment in the project root directory (`.venv`) by executing the following command:
   > _This step will automatically install all [baseline project requirements](./tools/requirements.txt) in the virtual 
   > environment, upgrade all core Python packages (e.g., `setuptools`, `pip`, and `build`) to the latest version, and
   > install the [`terraform_runner`](./wrapper-scripts/terraform_runner) package in editable mode._
   ```shell
   ❯ make venv
   [...]
   Building wheels for collected packages: terraform-runner
   Building editable for terraform-runner (pyproject.toml) ... done
   Created wheel for terraform-runner: filename=terraform_runner-1.0.0-0.editable-py3-none-any.whl size=10592 sha256=b247abd72f4e101b98cb04b8933822cc917461132ec436d85a73686a8f549582
   Stored in directory: /private/var/folders/29/fg_zrvhs7c9ftv3n6pnp0yfh0000gr/T/pip-ephem-wheel-cache-bmp24orp/wheels/31/c6/a2/4544d1f14fe49ce67ea68109c29fb404dd2026299eae488c69
   Successfully built terraform-runner
   Installing collected packages: terraform-runner
   Successfully installed terraform-runner-1.0.0
   ```

### Deploy Bootstrap Resources
In this step, you will deploy the S3 bucket used to store the Terraform Reference Engine templates and binary 
distribution artifacts in your AWS environment. This project includes an [AWS CloudFormation template](cfn-templates/Bootstrap.yaml) 
that you can use to create a properly configured S3 bucket. 

1. Create a new AWS CloudFormation stack using the [bootstrap template](./cfn-templates/Bootstrap.yaml) by executing 
   the following command:
   ```shell
   ❯ aws cloudformation create-stack \
       --stack-name Bootstrap-TRE \
       --template-body file://cfn-templates/Bootstrap.yaml \
       --region "${AWS_REGION}"
   ```
2. This stack creates an S3 bucket in your AWS environment using a standard name prefix (e.g., `terraform-engine-bootstrap`) 
   with your 12-digit account ID and region appended. Once the CloudFormation stack has been successfully created, you 
   can determine the bucket name created in your environment with the following command:
   ```shell
   ❯ export BOOTSTRAP_BUCKET=$(aws cloudformation describe-stacks \
       --stack-name Bootstrap-TRE \
       --region "${AWS_REGION}" \
       --output text \
       --query 'Stacks[].Outputs[1].OutputValue'
     ) && echo "${BOOTSTRAP_BUCKET}"
   terraform-engine-bootstrap-123456789012-us-east-2
   ```

### Build Code Packages 
In this step, you will build the `terraform_runner` Python package in your local environment and build the AWS Lambda
Python and Go functions that the Terraform Reference Engine uses for its backend services and orchestration using 
Docker build containers.

1. Initiate a local build of the `terraform_runner` Python package and a containerized build of the TRE Lambda 
   functions by executing the following command:
   ```shell
   ❯ make build

   Successfully built terraform_runner-1.0.0.tar.gz and terraform_runner-1.0.0-py3-none-any.whl
   upload: wrapper-scripts/dist/terraform_runner-1.0.0-py3-none-any.whl to s3://terraform-engine-bootstrap-123456789012-us-east-2/dist/terraform_runner-1.0.0-py3-none-any.whl
   Starting Build use cache                                                                                                                                                                                                                                                              
   Starting Build inside a container 
   [...]
   Build Succeeded
   Built Artifacts  : .aws-sam/build
   Built Template   : .aws-sam/build/template.yaml
   ```
2. The `terraform_runner` binary distribution artifact will be automatically uploaded to the bootstrap S3 Bucket 
   created in the previous step. You can verify this by executing the following command:
   ```shell
   ❯ aws s3 ls "s3://${BOOTSTRAP_BUCKET}/dist/"
   2023-08-08 16:44:21      18532 terraform_runner-1.0.0-py3-none-any.whl
   ```

### Deploy the Terraform Reference Engine
In this step, you will use the AWS SAM CLI to deploy the Terraform Reference Engine to your AWS environment using 
the TRE infrastructure template (.aws-sam/packaged.yaml) built by the `make build` target executed above.

1. If the Terraform Reference Engine has already been deployed to the AWS environment, you will want to take some 
   additional steps before updating your environment. The project contains a convenience target in the [Makefile](./Makefile) 
   that will help you check if there is a pre-existing TRE deployment:
   ```shell
   ❯ make check-stack-exists
   CloudFormation Stack Name: SAM-TRE
   Terraform Reference Engine is DEPLOYED in AWS account 123456789012 and region us-east-2.
   
   ❯ make check-stack-exists
   CloudFormation Stack Name: SAM-TRE
   Terraform Reference Engine is NOT DEPLOYED in AWS account 123456789012 and region us-east-2.
   make: *** [check-stack-exists] Error 1
   ```
2. _If the Terraform Reference Engine check returns a `DEPLOYED` state_, execute the following command to pause 
   processing of new TRE provisioning requests and gracefully drain and terminate all TRE execution instances, waiting 
   for any active TRE provisioning requests to complete.
   ```shell
   ❯ ./tools/manage-terraform-engine.py \
       --region "${AWS_REGION}" \
       --action stop \
       --auto-approve
   2023-08-09T09:59:27Z [INFO] - Checking the status of the Terraform Reference Engine in AWS account '123456789012' and region 'us-east-2'
   2023-08-09T09:59:28Z [INFO] - Terraform Reference Engine Status: 'Enabled'
   2023-08-09T09:59:28Z [INFO] - Stopping the Terraform Reference Engine from processing new requests
   [...]
   2023-08-09T10:00:06Z [INFO] - Waiting for any currently running Terraform Reference Engine executions to complete
   2023-08-09T10:00:07Z [INFO] - Initiating a terminate operation for the following TRE execution instances: ['i-0f12345e0f123aaaa']
   2023-08-09T10:00:08Z [INFO] - Suspending the following scaling processes for auto scaling group 'TerraformAutoscalingGroup': ['Launch', 'ReplaceUnhealthy']
   2023-08-09T10:00:08Z [INFO] - Successfully initiated termination for 1 TRE execution instances
   [...]
   2023-08-09T10:00:54Z [INFO] - Checking the status of the Terraform Reference Engine in AWS account '123456789012' and region 'us-east-2'
   2023-08-09T10:00:55Z [INFO] - Terraform Reference Engine Status: 'Disabled'
   2023-08-09T10:00:55Z [INFO] - The Terraform Reference Engine has been successfully stopped, any new requests will remain in their SQS queues until restarted or they timeout
   2023-08-09T10:00:55Z [INFO] - Total execution time: 89s
   ```
3. Retrieve the current version of the `terraform_runner` Python package:
   ```shell
   ❯ export TF_RUNNER_VER=$(head -n 1 ./wrapper-scripts/terraform_runner/__init__.py | awk '{print $3}' | xargs)
   ```
4. Deploy or update the Terraform Reference Engine in your AWS environment using the AWS SAM CLI:
   ```shell
   ❯ sam deploy \
       --config-file ./samconfig.toml \
       --template-file ./.aws-sam/packaged.yaml \
       --region "${AWS_REGION}" \
       --s3-bucket "${BOOTSTRAP_BUCKET}" \
       --parameter-overrides "ParameterKey=TerraformRunnerVersion,ParameterValue=${TF_RUNNER_VER}"
   
   Deploying with following values
   ===============================
   Stack name                   : SAM-TRE
   Region                       : us-east-2
   Confirm changeset            : False
   Disable rollback             : False
   Deployment s3 bucket         : terraform-engine-bootstrap-123456789012-us-east-2
   Capabilities                 : ["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"]
   Parameter overrides          : {"TerraformRunnerVersion": "1.0.0"}
   Signing Profiles             : {}

   Initiating deployment
   =====================
   Waiting for changeset to be created..
   Changeset created successfully. arn:aws:cloudformation:us-east-2:123456789012:changeSet/samcli-deploy1691606704/be73dd87-2c9a-4bbc-bd3d-756e1bbe83b4
   2023-08-09 11:45:34 - Waiting for stack create/update to complete
   [...]
   Successfully created/updated stack - SAM-TRE in us-east-2
   ```
5. If you previously disabled the Terraform Reference Engine in your AWS environment in Step 2 above, you need to 
   re-enable the processing of TRE provisioning requests by executing the following command:
   > _This step is not necessary if you are deploying Terraform Reference Engine for the first time in your AWS 
   > environment._
   ```shell
   ❯ ./tools/manage-terraform-engine.py \
       --region "${AWS_REGION}" \
       --action start \
       --auto-approve
   2023-08-09T11:57:19Z [INFO] - Checking the status of the Terraform Reference Engine in AWS account '123456789012' and region 'us-east-2'
   2023-08-09T11:57:19Z [INFO] - Terraform Reference Engine Status: 'Disabled'
   2023-08-09T11:57:19Z [INFO] - Starting Terraform Reference Engine execution instances
   2023-08-09T11:57:20Z [INFO] - Resuming the following scaling processes for auto scaling group 'TerraformAutoscalingGroup': ['Launch', 'ReplaceUnhealthy']
   2023-08-09T11:57:20Z [INFO] - Waiting for TRE execution instances to reach one of the following desired states: ['running']
   2023-08-09T11:59:21Z [INFO] - All TRE execution instances have reached one of the desired states
   2023-08-09T11:59:38Z [INFO] - Resuming the processing of new requests by the Terraform Reference Engine
   [...]
   2023-08-09T12:00:16Z [INFO] - Checking the status of the Terraform Reference Engine in AWS account '123456789012' and region 'us-east-2'
   2023-08-09T12:00:17Z [INFO] - Terraform Reference Engine Status: 'Enabled'
   2023-08-09T12:00:17Z [INFO] - The Terraform Reference Engine has been successfully started, any new requests received or requests currently in the TRE SQS queues will be processed
   2023-08-09T12:00:17Z [INFO] - Total execution time: 180s
   ```
</details>

---

## Troubleshooting Installation Errors

This section addresses some of the common errors that users may encounter during installation or updating of the 
Terraform Reference Engine in their AWS environments. 

<details>
   <summary><b>Security Group Replacement</b></summary>

   ### Security Group Replacement
   > [!NOTE]
   > _If you use the automated deployment tooling provided by this project ([`deploy-terraform-engine.sh`](./tools/deploy-terraform-engine.sh)),
   > the resource replacement and dependency violation errors described in this section are automatically handled for you._ 

   When a user is updating an existing deployment of the Terraform Reference Engine, replacement of existing resources 
   such as the security group used by the TRE execution instances _may_ be necessary. However, you cannot delete a 
   security group that's associated with EC2 instances that are in the `running` or `stopped` state, and 
   attempts to do so will result in the following error message: 
   ```shell
   resource sg-xxxxxxxx has a dependent object (Service: AmazonEC2; Status Code: 400; Error Code: DependencyViolation;
   ```

   To resolve this error: 
   1. Terminate all TRE execution instances (i.e., EC2 instances named `TerraformExecutionInstance`) and ensure no new 
      instances are launched while performing the update. The easiest way to accomplish this is to execute the following 
      command, replacing `<AWS_REGION>` with the correct region for your AWS environment:
      ```shell
      ❯ ./tools/manage-terraform-engine.py \
          --region <AWS_REGION> \
          --action stop \
          --auto-approve
      ```
   2. This command will stop the existing Terraform Reference Engine from processing new TRE provisioning requests, 
      gracefully drain all TRE execution instances, and prevent the auto scaling group from launching new TRE execution 
      instances until re-enabled.
   3. Initiate the update of the Terraform Reference Engine.
   4. Once the update operation has completed successfully, re-enable the Terraform Reference Engine environment by 
      executing the following command, replacing `<AWS_REGION>` with the correct region for your AWS environment:
      ```shell
      ❯ ./tools/manage-terraform-engine.py \
          --region <AWS_REGION> \
          --action start \
          --auto-approve
      ```
</details>

---

## Create and Provision an AWS Service Catalog Product
> [!IMPORTANT]
> _Unless otherwise specified, all commands should be executed from the [Terraform Example](example) directory._

In addition to the steps outlined below, you can find more information about creating and provisioning Terraform 
products in AWS Service Catalog from the [Getting Started with Terraform Open Source guide](https://docs.aws.amazon.com/servicecatalog/latest/adminguide/getstarted-Terraform.html)
and the [Self-Service Provisioning of Terraform Open-Source Configurations with AWS Service Catalog blog post](https://aws.amazon.com/blogs/aws/new-self-service-provisioning-of-terraform-open-source-configurations-with-aws-service-catalog/).
 
This project includes an example [Terraform module](example/terraform-example-bucket) that you can use to create your 
first Terraform Service Catalog product. The example product will create an S3 bucket in an end user AWS account that 
is configured for secure cross-account access by a designated central security operations AWS account. The [Terraform 
Example Makefile](example/Makefile) contains a number of convenience targets to help you easily deploy or remove the 
example in your AWS environment.

### Automated Deployment of the Terraform Example Module

1. Ensure your local environment passes all prerequisite checks and that you have properly set the environment
   variables required to deploy the Terraform Example product by executing the following command from within the 
   [Terraform Example directory (./example)](example):
   ```shell
   ❯ make check-prerequisites
   AWS Account: 123456789012
   AWS Region: us-east-2
   Directory Name: example
   All prerequisites are installed and configured properly.
   ```
   > [!IMPORTANT]
   > _Make sure you are executing in your Service Catalog central hub account and the correct region and that the 
   > directory name is `example` before continuing._  

2. Deploy the Terraform Example product to your Service Catalog central hub account by executing the following command:
   ```shell
   ❯ make create-terraform-example
   Building provisioning artifact and copying to the bootstrap S3 bucket.
      - Provisioning Artifact: s3://terraform-engine-bootstrap-123456789012-us-east-2/dist/terraform-example-bucket.tar.gz
   Creating the IAM role in AWS account 123456789012 for the Service Catalog launch constraint.
      - Launch Role: arn:aws:iam::123456789012:role/SCLaunchRoleTerraformBucketExample
   Creating the Service Catalog product in AWS account 123456789012.
      - Service Catalog Product: prod-o6ry72lee5j5y
   Creating the Service Catalog portfolio in AWS account 123456789012.
      - Service Catalog Portfolio: port-gyl5agftgwzsk
   Associating the Service Catalog product with the portfolio in AWS account 123456789012.
      - Product Association: prod-o6ry72lee5j5y with port-gyl5agftgwzsk
   Creating launch constraint for the Service Catalog product and portfolio in AWS account 123456789012.
      - Service Catalog Constraint: cons-ambp22i6kfiik
   ```
   The `create-terraform-example` target automatically handles the following steps for you:
      - Packages the Terraform Example module into a `tar.gz` provisioning artifact and copies it to the TRE bootstrap S3 bucket. 
      - Creates an IAM role that is properly configured for use as the Terraform Example launch role in your Service Catalog central hub account.
      - Creates a Service Catalog product and portfolio for the Terraform Example module.
      - Associates the Service Catalog product with the portfolio and creates the appropriate launch constraint.

### Sharing the Terraform Example Portfolio

Once you have successfully deployed the Terraform Example module to your Service Catalog central hub account, you can 
make the Terraform Example product available to end users by [sharing the Service Catalog portfolio](https://docs.aws.amazon.com/servicecatalog/latest/adminguide/catalogs_portfolios_sharing_how-to-share.html) 
and [granting access](https://docs.aws.amazon.com/servicecatalog/latest/adminguide/catalogs_portfolios_users.html). 
The [Terraform Example Makefile](example/Makefile) contains convenience targets to help you easily grant portfolio 
access to IAM role principals and share the portfolio to AWS Organizations OUs.

In the following steps, we will share the Terraform Example portfolio with all AWS accounts within an AWS Organizations 
OU and grant access to any user who is authorized to assume the IAM role that corresponds to an IAM Identity Center 
permission set named `AccountOwners`:

1. To grant access to all users authorized to access the desired permission set role, execute the following 
   command, replacing the pattern in `SHARED_ROLE_NAME` with the appropriate value for your environment:
   ```shell
   ❯ make grant-portfolio-access SHARED_ROLE_NAME="AWSReservedSSO_AccountOwners_*"
   Granting access to the Service Catalog portfolio in 123456789012 to any IAM roles matching the following pattern: arn:aws:iam:::role/**/AWSReservedSSO_AccountOwners_*
     - Granted Portfolio Access: arn:aws:iam:::role/**/AWSReservedSSO_AccountOwners_*
   ```
2. Repeat Step 1 for any additional IAM principals that should be granted access to the Terraform Example portfolio. 
3. To share the Service Catalog portfolio to all AWS accounts in an AWS Organizations OU, execute the following command, 
   replacing the ID in `SHARED_OU_ID` with the appropriate value for your environment:
   ```shell
   ❯ make share-portfolio SHARED_OU_ID=ou-olqy-7puk9u2d                          
   Sharing the Service Catalog portfolio in 123456789012 with the AWS Organizations OU: ou-olqy-7puk9u2d
     - Portfolio Share: ou-olqy-7puk9u2d
   ```
4. Repeat Step 3 for any additional AWS Organizations OUs where the Terraform Example portfolio should be shared.

### Launch Role Provisioning 

In order to successfully provision the Terraform Example product, the [launch role](https://docs.aws.amazon.com/servicecatalog/latest/adminguide/getstarted-launchrole-Terraform.html) 
must exist in each end user AWS account to which the Terraform Example portfolio is shared. If you followed the steps 
above, the launch role was automatically created for you in the Service Catalog central hub account. 

This project includes a [CloudFormation template](example/terraform-example-launch-role.yaml) which you can use with 
[CloudFormation StackSets](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/what-is-cfnstacksets.html) to 
provision the Terraform Example launch role. You can also use the convenience targets in the [Terraform Example Makefile](example/Makefile) 
to deploy the Terraform Example launch role to one or more AWS accounts in which you want to test:

1. Configure your shell environment with the appropriate AWS credentials for the end user AWS account where you want 
   to deploy the Terraform Example launch role.
2. Verify your local environment passes all prerequisite checks and that your AWS region matches the region in which 
   you deployed the Terraform Reference Engine by executing the following command:
   ```shell
   ❯ make check-prerequisites                
   AWS Account: 987654321012
   AWS Region: us-east-2
   Directory Name: example
   All prerequisites are installed and configured properly.
   ```
3. Deploy the launch role to the targeted end user AWS account by executing the following command:
   ```shell
   ❯ make create-launch-role                  
   Creating the IAM role in AWS account 987654321012 for the Service Catalog launch constraint.
     - Launch Role: arn:aws:iam::987654321012:role/SCLaunchRoleTerraformBucketExample-us-east-2
   ```
4. Repeat Steps 1-3 for any other end user AWS accounts where you want to deploy the Terraform Example launch role.
   
### Remove the Terraform Example Product

When you are done testing and wish to remove the Terraform Example product from your AWS environment, you can use 
the convenience targets in the [Terraform Example Makefile](example/Makefile) to help you easily complete the required 
tasks.

1. Ensure your local environment passes all prerequisite checks and that you have properly set the environment 
   variables required to remove the Terraform Example product by executing the following command:
   ```shell
   ❯ make check-prerequisites                
   AWS Account: 123456789012
   AWS Region: us-east-2
   Directory Name: example
   All prerequisites are installed and configured properly.
   ```
   > [!IMPORTANT]
   > _Make sure you are executing in your Service Catalog central hub account and the correct region._ 
2. Remove the Terraform Example product from your Service Catalog central hub account by executing the following 
   command:
   ```shell
   ❯ make delete-terraform-example                                                        
   Removing all Service Catalog portfolio shares in AWS account 123456789012.
     - Removed Portfolio Share: ou-olqy-7puk9u2d
   Revoking access to the Service Catalog portfolio in 123456789012 for all defined IAM role patterns.
     - Revoked Portfolio Access: arn:aws:iam:::role/**/AWSReservedSSO_AccountOwners_*
   Removing the Service Catalog product association with the portfolio in AWS account 123456789012.
     - Deleted Product Association: prod-it6iylgwgrc72 from port-zsskaaxwu2nfc
   Deleting the Service Catalog portfolio from AWS account 123456789012.
     - Deleted Service Catalog Portfolio: port-zsskaaxwu2nfc
   Deleting the Service Catalog product from AWS account 123456789012.
     - Deleted Service Catalog Product: prod-it6iylgwgrc72
   Deleting the IAM role in AWS account 123456789012 used for the Service Catalog launch constraint.
     - Deleted Launch Role: arn:aws:iam::123456789012:role/SCLaunchRoleTerraformBucketExample-us-east-2
   ```
   The `delete-terraform-example` target automatically handles the following steps for you:
      - Revokes the sharing of the Terraform Example portfolio for all defined AWS Organizations OUs.
      - Revokes access to the Terraform Example portfolio for all defined IAM principals. 
      - Disassociates the Terraform Example product from the Terraform Example portfolio and deletes the portfolio.
      - Deletes the Terraform Example product.
      - Deletes the IAM role used as the Terraform Example launch role from your Service Catalog central hub account.

   > _If you did not provision the Terraform Example launch role in any additional AWS accounts, you should stop here._

3. Configure your shell environment with the appropriate AWS credentials for one of the end user AWS accounts where you 
   previously provisioned the Terraform Example launch role.
4. Delete the launch role from the targeted end user AWS account by executing the following command:
   ```shell
   ❯ make delete-launch-role                  
   Creating the IAM role in AWS account 987654321012 for the Service Catalog launch constraint.
     - Launch Role: arn:aws:iam::987654321012:role/SCLaunchRoleTerraformBucketExample-us-east-2
   ```
5. Repeat Steps 3 & 4 for any other end user AWS accounts where you previously provisioned the Terraform Example 
   launch role.

---

## Architecture Overview

### Purpose

The Service Catalog Terraform Reference Engine is a project that allows product cataloging and provisioning using Terraform as the choice for infrastructure as code.

### What Is a TERRAFORM_OPEN_SOURCE Product Engine?

Service Catalog supports a product type called TERRAFORM_OPEN_SOURCE. Customers use this product type to catalog and provision products where the implementation of the product is built by the customer. This product implementation is known as an engine.

* When a user creates a new product or provisioning artifact of type TERRAFORM_OPEN_SOURCE, Service Catalog stores the provisioning artifact but does not validate it. 
* When DescribeProvisioningParameters is called on a TERRAFORM_OPEN_SOURCE product, Service Catalog calls a Lambda function provided by the customer to parse the parameters from the artifact.
* When a user starts a provisioning workflow for a TERRAFORM_OPEN_SOURCE product, Service Catalog publishes a message to an agreed-upon queue. The engine consumes these messages, and for each it provisions, updates, or terminates the resources as described by the provisioning artifact. When the workflow is done, the engine calls back to Service Catalog to report results. 

In this reference architecture, we have built a Terraform Open Source product engine for Terraform. The provisioning artifacts will be Terraform configuration files written in Hashicorp Config Language (HCL). The creation and management of resources will be done using Terraform Open Source running on EC2 instances.

### Service Catalog Terraform Open Source Parameter Parser

The Terraform reference engine includes a Lambda function to parse variables in the provisioning artifact and return them to Service Catalog. The function is invoked when the end user calls the Service Catalog DescribeProvisioningParameters API.

The Service Catalog Terraform Open Source Parameter Parser is a Lambda function written in Go. It uses the Hashicorp Config Inspect library to inspect HCL files: https://github.com/hashicorp/terraform-config-inspect

#### Artifact Specification

Only files with .tf filename extension in the zipped .tar.gz provisioning artifact would be parsed. Files in the .tf.json format are not supported.

#### Launch Role

The Service Catalog Terraform Open Source Parameter Parser assumes the provided launch role to download the artifact if a launch role is provided in the payload. If no launch role is provided, parameter parser will use the default lambda execution role ServiceCatalogTerraformOSParameterParserRole credentials to download the artifact.

If provided, the launch role arn must be a valid IAM arn that has access to the artifact and is assumable by the parser lambda.

#### Override Files

The Service Catalog Terraform Open Source Parameter Parser parses files with override.tf suffix as override files

Override files are loaded after normal configuration files with the merging behavior for parameters similar to the one described in Terraform documentation https://developer.hashicorp.com/terraform/language/files/override

Behavior when multiple override files define the same top-level variable block is undefined

Please also refer to the Override Files section under Limitations in the README below to understand the risks of using override files in Terraform Reference Engine

#### Exceptions

The Service Catalog Terraform Open Source Parameter Parser throws two types of exceptions: 
`ParserInvalidParameterException` and `ParserAccessDeniedException`:

- `ParserInvalidParameterException` is thrown when the provided input is invalid.

- `ParserAccessDeniedException` is thrown when the provided launch role cannot be assumed by the parser, or the 
   artifact cannot be accessed with the launch role.

## Provisioning Workflows

The Terraform reference engine contains workflows that implement Service Catalog provisioning functions.

### Provisioning Workflow Types

1. Provision/Update
1. Terminate

### Provisioning Workflow Components

Each provisioning workflow consists of the following components:

1. Inbound message SQS queue
1. Message handler Lambda function
1. Execution Step Functions state machine
1. SSM Run Command execution
1. Terraform state S3 bucket
1. Terraform execution EC2 autoscaling group

#### Inbound Message Queue

AWS Service Catalog publishes a message to an SQS queue for each provisioning operation. 

| Operation | Queue Name |
| --- | --- |
| Provision | ServiceCatalogTerraformOSProvisionOperationQueue |
| Update | ServiceCatalogTerraformOSUpdateOperationQueue |
| Terminate | ServiceCatalogTerraformOSTerminateOperationQueue |

#### Message Handler Lambda Functions

The Terraform reference engine contains Lambda message handler functions that consume messages from the inbound queues. The job of each function is to use the message contents as input to start the corresponding workflow's state machine.

Note that there is one handler for both provision and update messages. This is because provision and update operations use the same provision/update workflow. Terminate messages have a separate handler and a separate workflow.

#### State Machines

Each workflow has a Step Functions state machine responsible for overall logic of the workflow. Although they have some differences, the provision/update state machine and terminate state machine follow similar steps.

1. Select an EC2 instance from the autoscaling group.
1. Use SSM Run Command to execute Terraform work on the EC2 instance.
1. Poll Run Command for results of the Run Command execution.
1. When Run Command has finished, gather the workflow results and report them to Service Catalog.

#### SSM Run Command Execution

The Run Command execution starts a script on one of the EC2 instances to do the work of Terraform apply or destroy, depending on the workflow. In the Terraform Reference Engine, a Python package named terraform_runner handles the CLI commands to complete Terraform apply or destroy.

#### Terraform Apply

For the provision/update workflow, the terraform_runner package performs these steps.

1. Create a temporary directory to serve as a Terraform workspace
1. Assume the launch role and download the provisioning artifact
1. Override parameters, assume-role, backend, and tags. The Tag override will be the tracer tag explained in the Limitations section below.
1. Execute Terraform apply
1. Clean up the temporary directory

#### Terraform Destroy

For the terminate workflow, the terraform_runner package performs these steps.

1. Create a temporary directory to serve as a Terraform workspace
1. Override assume-role and backend
1. Execute Terraform destroy
1. Clean up the temporary directory

## Quality Assurance

Unit tests are included for each Lambda function as well as for the terraform_runner Python package.

## Attributions

1. [Terraform](https://github.com/hashicorp/terraform)
1. [Hashicorp Terraform Config Inspect library](https://github.com/hashicorp/terraform-config-inspect)
1. [Original 2018 Service Catalog Terraform Reference Architecture](https://github.com/aws-samples/aws-service-catalog-terraform-reference-architecture)
1. [Python virtual environment](https://docs.python.org/3/library/venv.html)

## Limitations

### Artifact File Types

All provisioning artifacts must be in tar.gz format and have a filename extension of .tar.gz. Inside the tar.gz file, the Terraform config files must be in .tf format. The .tf.json format is not supported.

When creating the tar.gz file, be sure that the root-module files are at the root directory of the archive. Some archiving tools default to putting the files into a top-level directory. If that happens, the engine cannot determine the root module from local modules in subdirectories.

### Override Files

The Terraform Reference Engine adds some override files to each configuration before running Terraform CLI commands. Therefore, if your configuration conflicts with any of the below overrides, the behavior of the CLI commands on that configuration will be undefined. We strongly recommend that you avoid including override files in your provisioning artifact.

### Backend Overrides

The engine adds a file named backend_override.tf.json. This sets the Terraform state bucket S3 to the state bucket created from the Sam template and sets the S3 key to a name that uniquely identifies the provisioned product.

Example:

```
{
    "terraform": {
        "backend": {
            "s3": {
                "bucket": "sc-terraform-engine-state-<your account ID>",
                "key": "pp-1234",
                "region": "us-east-1"
            }
        }
    }
}
```

The engine does not include DynamoDB state locking in the backend configuration. This is not needed for two reasons.

1. Service Catalog does not allow concurrent operations on a provisioned product.
1. The engine has safeguards to prevent multiple workflow executions when duplicate messages are received. The combination of the provisioned product ID and record ID generated by Service Catalog are used to recognize duplicate messages and to prevent duplicate executions.

### Variable Override

The engine adds a file named variable_override.tf.json. This file sets variable defaults based on the parameters provided by the end user to Service Catalog when performing a provision or update operation.

Example:

```
{
    "variable": {
        "key1": {
            "default": "parameter-value1"
        },
        "key2": {
            "default": "parameter-value2"
        }
    }
}
```

### Provider Override

The engine adds a file named provider_override.tf.json. The engine sets several overrides in this file:

* The region in which the changes will be made. This is always the same region that the engine is deployed to.
* The assume role. This is always set to the Service Catalog launch role.
* The default tags. This is always set to a single tracer tag that is used by Service Catalog at the end of a provision or update operation to identify the resources belonging to the provisioned product.

Example:

```
{
    "provider": {
        "aws": {
            "region": "us-east-1",
            "assume_role": {
                "role_arn": "arn:aws:iam::111122223333:role/SCLaunchRoleTerraformExample",
                "session_name": "pp-1234_MyProvisioned_product"
            },
            "default_tags": {
                "tags": {
                    "SERVICE_CATALOG_TERRAFORM_INTEGRATION-DO_NOT_DELETE": "pp-1234"
                }
            }
        }
    }
}
```

The engine overrides the "aws" provider. Other providers are not supported. 

If you do include other providers in your Terraform configuration, be sure they are not writing to the local file system outside the current working directory. The engine creates a unique working directory for each provisioned product on the EC2 instance. If the Terraform configuration writes outside this directory, those files could interfere with processes working on other provisioned products on the same instance.

The tag SERVICE_CATALOG_TERRAFORM_INTEGRATION-DO_NOT_DELETE will be applied to all resources provisioned by the engine. Do not modify this tag. It is required for Service Catalog to maintain a resource group containing the resources for the provisioned product.

### Resource Timeouts

Service Catalog will time out your provisioning operation if it runs too long. See the Service Catalog documentation for the maximum duration of a provisioning operation.

If you include resource timeouts in your Terraform configuration, the timeout with the shorter duration will take effect. 

### Parameter Parser

#### Parsing Large Provisioning Artifacts

Due to AWS Lambda memory size constraint, large provisioning artifacts compressed using standard .tar.gz algorithm over 500 KB might fail to be parsed.

MemorySize setting for the parameter parser can be adjusted up to 10240 MB by overriding ParameterParserLambdaMemorySize parameter in the template in order to accommodate the need for parsing very large provisioning artifacts.

#### Parser Output

Parameter parser parses Terraform variable arguments including name, default, type, description and sensitive. Specifically, validation and nullable fields are not parsed.

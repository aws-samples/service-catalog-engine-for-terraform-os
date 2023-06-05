# AWS Service Catalog Engine for Terraform open source

The AWS Service Catalog Terraform Reference Engine (TRE) provides an example for you to configure and install a Terraform open source engine in your AWS Service Catalog administrator account. With the engine installed into your account, you can use Service Catalog as a single tool to organize, govern, and distribute your Terraform configurations within AWS.
For more information about Terraform open source and AWS Service Catalog, see [Getting started with Terraform open source.](https://docs.aws.amazon.com/servicecatalog/latest/adminguide/getstarted-Terraform.html)

# Pre-requisites

The installation can be done from any Linux or Mac machine.

## Install tools

1. Install AWS SAM CLI: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html
1. Install Docker (only required if you want to run the Lambda functions in your development environment): https://docs.docker.com/engine/install/
1. Install AWS CLI https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
1. Install Go https://go.dev/doc/install
1. Install Python 3.9. Sam will require this exact version even if you have a newer version. https://www.python.org/downloads/release/python-3913/

# Automatically Install the Terraform Reference Engine

The project includes a set of scripts to automatically install a new environment or update an existing environment. The script does the following:
1. Performs all installation steps.
1. If the installation is updating an existing environment, it safely replaces the EC2 instances.
    1. Pauses SQS message processing
    1. Waits for all state machine executions to finish
    1. Replaces EC2 instances
    1. Resumes SQS message processing.

The automated installation requires that the following are available on your local machine. If they are not available, please follow the instructions below for manual installation.

1. bash
1. jq

The instance replacement process can take a long time if you have long-running provisioning operations in flight.

The automated installation  assumes you are using the default profile to store your AWS Credentials. Follow https://docs.aws.amazon.com/sdk-for-java/v1/developer-guide/setup-credentials.html to set up credentials.

You can install the engine or update an existing engine by doing the following:

1. Git clone the project
1. From the root directory of the project, run ./bin/bash/deploy-tre.sh -r <region>
    * The region set in your default profile is not used during the automated installation. Instead, you will provide the region when executing this command.

# Manually Install the Terraform Reference Engine

If you prefer to install the engine manually, perform the steps in this section. These steps do not need to be performed if you used the automated script in the previous section.

## Setup Your Environment

1. Git clone the project.
1. Setup the following environment variables:
    ```
    AWS_ACCOUNT_ID=<YOUR AWS ACCOUNT ID>
    AWS_REGION=<YOUR REGION OF CHOICE>
    ```

The manual instructions assume you are using the default profile to store your AWS Credentials and region. Follow https://docs.aws.amazon.com/sdk-for-java/v1/developer-guide/setup-credentials.html to set up credentials and region.

## Build the code

### Build the ServiceCatalogTerraformOSParameterParser function

1. Cd to the directory `lambda-functions/terraform_open_source_parameter_parser`
1. Run `go mod init terraform_open_source_parameter_parser` to initialize the terraform_open_source_parameter_parser Go module
1. Run `go env -w GOPROXY=direct`
1. Run `go mod tidy` to generate the required `go.mod` and `go.sum` files
1. Optional step: Run `go test` within the test containing directory to execute all unit tests in Go

### Create a python virtual environment
1. Create the virtual environment in directory `venv` by running the command `python3 -m venv venv`
1. Activate the newly created pythong virtual environment `. venv/bin/activate`

Note: Once done running all python commands call `deactivate` to stop using the virtual environment.

### Build the Lambda functions 

1. Cd to the root directory of the project.
1. Run this command to install a local copy of the Python libraries required for the lambdas.
    * `pip3 install -r lambda-functions/state_machine_lambdas/requirements.txt -t lambda-functions/state_machine_lambdas --upgrade`
1. Run `GOOS=linux GOARCH=amd64 CGO_ENABLED=0 sam build`
1. Optional step: Run `python3 -m unittest` within the test containing directory to execute all unit tests in python
1. Optional step: If you are a developer and want to invoke the Lambda functions locally, run `sam local invoke <Logical ID of the function>`

## Deploying to an AWS Account

### Create the bootstrap bucket

Use the Cloudformation console or CLI to create a stack using the Bootstrap.yaml template:

    ```
    AWS242TerraformReferenceEngine (package-root)
    └── cfn-templates
        └── Bootstrap.yaml
    ```

To use the CloudFormation CLI, run this example CLI command -

```
    aws cloudformation create-stack --stack-name Bootstrap-TRE --template-body file://cfn-templates/Bootstrap.yaml --capabilities CAPABILITY_NAMED_IAM
```

This will create a bucket named terraform-engine-bootstrap-<your_account_id>-<region>. Code build artifacts will be made available to the deployment process from this bucket.

### Deploy the Terraform CLI wrapper scripts

In this step we build the Python scripts that will run on EC2 instances to manage Terraform CLI commands. Then we upload them to the bootstrap bucket created in the previous step.

1. cd to the `wrapper-scripts` directory: `cd wrapper-scripts`
1. Install python wheel package: `pip install wheel`
1. Run: `python3 setup.py bdist_wheel`
1. Run: `aws s3 sync dist s3://terraform-engine-bootstrap-$AWS_ACCOUNT_ID-$AWS_REGION/dist`

### Deploy the Terraform reference engine

1. cd to the root directory of the project.
1. Run `sam deploy --s3-bucket terraform-engine-bootstrap-$AWS_ACCOUNT_ID-$AWS_REGION --stack-name SAM-TRE --capabilities CAPABILITY_NAMED_IAM`
1. The default settings can be overridden by passing the parameters in the `template.yaml`. 
   * Example command for updating the default VPC setting -
      `--parameter-overrides VpcCidr="<Your_VpcCidr>" PublicSubnet1CIDR="<Your_PublicSubnet1CIDR>" PrivateSubnet1CIDR="<Your_PrivateSubnet1CIDR>"`
   * Example command for updating the default EC2 instance type setting -
     `--parameter-overrides EC2InstanceType="<Your_EC2InstanceType>"`

## Replace Current EC2 Instances

If you are updating an existing environment, you will need to replace the EC2 instances so the new instances will pick up the latest code. 

To do this manually, you can run the instance replacement script.

```
cd bin/bash
pip3 install boto3
export AWS_REGION=<your region>
python3 replace-ec2-instances.py 
```

Note: The instance replacement process can take a long time if you have long-running provisioning operations in flight.

# Troubleshooting Installation Errors

### Security Group Replacement

If you see this error during an update of the SAM-TRE stack:

`resource sg-xxxxxxxx has a dependent object (Service: AmazonEC2; Status Code: 400; Error Code: DependencyViolation;`

Solution: Terminate your EC2 instances named TerraformExecutionInstance. Then rerun the failed command.

# Create and Provision a Service Catalog Product

In addition to the steps included in this readme, more information about creating and provisioning a service catalog product can be found here: https://docs.aws.amazon.com/servicecatalog/latest/adminguide/getstarted-Terraform.html


## Create a Product

1. Create a product in Service Catalog 
    * Use TERRAFORM_OPEN_SOURCE as the product type. 
    * Use TERRAFORM_OPEN_SOURCE as the provisioning artifact type.
    * Use a .tar.gz file containing your Terraform config as the provisioning artifact file.


## Add a Launch Role

Every terraform-open-source product must have a launch constraint that indicates the IAM role to be used for provisioning the product's resources. This role is known as the "launch role." 

An example launch role is here: ```cfn-templates/TerraformProvisioningAccount.yaml```

The Terraform Reference Engine has the following requirements for the launch role.
1. Grant sts:AssumeRole permission to some Terraform Reference Engine IAM roles.
    * The role used for parsing parameters in the provisioning artifact. This role is named ServiceCatalogTerraformOSParameterParserRole-<region>.
    * The role used for running Terraform commands. the named of this role is TerraformExecutionRole-<region>.
    * When adding these roles to the IAM policy, use a Condition block with the StringLike operator on aws:PrincipalArn, rather than setting these role arns directly in the Resource block. See the example listed above.

In addition, Service Catalog has requirements for each terraform-open-source product's launch role.
https://docs.aws.amazon.com/servicecatalog/latest/adminguide/getstarted-launchrole-Terraform.html

1. Grant sts:AssumeRole to the Service Catalog service principal.
1. Include permissions to manage tagging and resource grouping of the provisioned resources.
1. Grant s3:GetObject to access the Service Catalog bucket where provisioning artifact files are made available. You can use a Condition block to limit the resource to buckets with the tag key "servicecatalog:provisioning" and value "true." See the above example.

## Grant Access to the Product

1. Put the product in a portfolio and grant access to an IAM user, group, or role. This IAM principal is known as the Service Catalog end user.
1. Optionally, you can share the portfolio to other accounts.

## Provision the Product

Now the Service Catalog end user can call these provisioning operations on the product:

1. DescribeProvisioningParameters
1. ProvisionProduct
1. UpdateProvisionedProduct
1. TerminateProvisionedProduct

The Terraform Reference Engine will perform these operations in the account where the product was created. If the launch role is in a different account, the resources will be provisioned in that account.

# Architecture Overview

## Purpose

The Service Catalog Terraform Reference Engine is a project that allows product cataloging and provisioning using Terraform as the choice for infrastructure as code.

## What Is a TERRAFORM_OPEN_SOURCE Product Engine?

Service Catalog supports a product type called TERRAFORM_OPEN_SOURCE. Customers use this product type to catalog and provision products where the implementation of the product is built by the customer. This product implementation is known as an engine.


* When a user creates a new product or provisioning artifact of type TERRAFORM_OPEN_SOURCE, Service Catalog stores the provisioning artifact but does not validate it. 
* When DescribeProvisioningParameters is called on a TERRAFORM_OPEN_SOURCE product, Service Catalog calls a Lambda function provided by the customer to parse the parameters from the artifact.
* When a user starts a provisioning workflow for a TERRAFORM_OPEN_SOURCE product, Service Catalog publishes a message to an agreed-upon queue. The engine consumes these messages, and for each it provisions, updates, or terminates the resources as described by the provisioning artifact. When the workflow is done, the engine calls back to Service Catalog to report results. 

In this reference architecture, we have built a Terraform Open Source product engine for Terraform. The provisioning artifacts will be Terraform configuration files written in Hashicorp Config Language (HCL). The creation and management of resources will be done using Terraform Open Source running on EC2 instances.

## Service Catalog Terraform Open Source Parameter Parser

The Terraform reference engine includes a Lambda function to parse variables in the provisioning artifact and return them to Service Catalog. The function is invoked when the end user calls the Service Catalog DescribeProvisioningParameters API.

The Service Catalog Terraform Open Source Parameter Parser is a Lambda function written in Go. It uses the Hashicorp Config Inspect library to inspect HCL files: https://github.com/hashicorp/terraform-config-inspect

### Usages

#### Artifact Specification

Only files with .tf filename extension in the zipped .tar.gz provisioning artifact would be parsed. Files in the .tf.json format are not supported.

#### Launch Role

The Service Catalog Terraform Open Source Parameter Parser assumes the provided launch role to download the artifact if a launch role is provided in the payload. If no launch role is provided, parameter parser will use the default lambda execution role ServiceCatalogTerraformOSParameterParserRole credentials to download the artifact.

If provided, the launch role arn must be a valid IAM arn that has access to the artifact and is assumable by the parser lambda.

### Override Files

The Service Catalog Terraform Open Source Parameter Parser parses files with override.tf suffix as override files

Override files are loaded after normal configuration files with the merging behavior for parameters similar to the one described in Terraform documentation https://developer.hashicorp.com/terraform/language/files/override

Behavior when multiple override files define the same top-level variable block is undefined

Please also refer to the Override Files section under Limitations in the README below to understand the risks of using override files in Terraform Reference Engine

### Exceptions

The Service Catalog Terraform Open Source Parameter Parser throws two types of exceptions: ParserInvalidParameterException and ParserAccessDeniedException

ParserInvalidParameterException is thrown when the provided input is invalid

ParserAccessDeniedException is thrown when the provided launch role cannot be assumed by the parser, or the artifact cannot be accessed with the launch role

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

# Attributions

1. [Terraform](https://github.com/hashicorp/terraform)
1. [Hashicorp Terraform Config Inspect library](https://github.com/hashicorp/terraform-config-inspect)
1. [Original 2018 Service Catalog Terraform Reference Architecture](https://github.com/aws-samples/aws-service-catalog-terraform-reference-architecture)
1. [Python virtual environment](https://docs.python.org/3/library/venv.html)

# Limitations

## Artifact File Types

All provisioning artifacts must be in tar.gz format and have a filename extension of .tar.gz. Inside the tar.gz file, the Terraform config files must be in .tf format. The .tf.json format is not supported.

When creating the tar.gz file, be sure that the root-module files are at the root directory of the archive. Some archiving tools default to putting the files into a top-level directory. If that happens, the engine cannot determine the root module from local modules in subdirectories.

## Override Files

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

## Resource Timeouts

Service Catalog will time out your provisioning operation if it runs too long. See the Service Catalog documentation for the maximum duration of a provisioning operation.

If you include resource timeouts in your Terraform configuration, the timeout with the shorter duration will take effect. 

## Parameter Parser

### Parsing Large Provisioning Artifacts

Due to AWS Lambda memory size constraint, large provisioning artifacts compressed using standard .tar.gz algorithm over 500 KB might fail to be parsed.

MemorySize setting for the parameter parser can be adjusted up to 10240 MB by overriding ParameterParserLambdaMemorySize parameter in the template in order to accommodate the need for parsing very large provisioning artifacts.

### Parser Output

Parameter parser parses Terraform variable arguments including name, default, type, description and sensitive. Specifically, validation and nullable fields are not parsed.

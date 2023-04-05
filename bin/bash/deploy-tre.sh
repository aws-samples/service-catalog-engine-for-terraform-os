#!/bin/bash
set -e

# Install dependencies & configure AWS credentials before executing script; see Readme.md for instructions
# Execute script from project root dir

usage() {
  echo "Usage: $0 -r <region> [-e <service-catalog-endpoint>] [-s <service-catalog-ssl-verification>]"
  echo "-r AWS region is required."
  echo "-e sets the endpoint for calls to Service Catalog. If not present, uses the default endpoint for the region."
  echo "-s sets SSL verification for calls to Service Catalog. Allowed values are true|false. Default is true."
  exit 1; 
}

while getopts ":r:e:s:" opt
do
  case "$opt" in
    r)
      AWS_REGION=$OPTARG
    ;;
    e)
      OVERRIDE_SERVICE_CATALOG_ENDPOINT="ParameterKey=ServiceCatalogEndpoint,ParameterValue=$OPTARG"
    ;;
    s)
      [[ $OPTARG == "true" || $OPTARG == "false" ]] || usage
      OVERRIDE_SERVICE_CATALOG_VERIFY_SSL="ParameterKey=ServiceCatalogVerifySsl,ParameterValue=$OPTARG"
    ;;
    *)
      usage
    ;;
  esac
done

[[ -z $AWS_REGION ]] && usage

RAW_AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --region $AWS_REGION)
AWS_ACCOUNT_ID=`echo $RAW_AWS_ACCOUNT_ID | sed s/\"//g`

BOOTSTRAP_BUCKET_NAME=terraform-engine-bootstrap-$AWS_ACCOUNT_ID-$AWS_REGION
SAM_STACK_NAME=SAM-TRE
SAM_DEPLOY_OUTPUT=/tmp/tre-sam-deploy-command.out
SCRIPT_DIR=./bin/bash


echo "AWS account: $AWS_ACCOUNT_ID"
echo "AWS region: $AWS_REGION"

if [ -d "venv" ]
then
    echo "Virtual environment directory already exists, Skipping creation of virtual environment"
else
    echo "Creating a Python virtual environment"
    # This assumes that you have python3.9 in your machine
    python3 -m venv venv
fi
. venv/bin/activate

echo "Building the ServiceCatalogTerraformOSParameterParser function"
cd lambda-functions/terraform_open_source_parameter_parser
rm -f go.mod
go mod init terraform_open_source_parameter_parser
go env -w GOPROXY=direct
go mod tidy

echo "Building the Lambda code"
cd ../.. # project root dir

# Install wheel because sam build seems to need it.
pip3 install wheel --upgrade

# Locally install required versions of boto3/botocore, so sam bundles it with the rest of the state machine lambda builds.
# We need to do this because the Lambda runtime environment lags on what version of boto it provides.
# https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html
pip3 install -r lambda-functions/state_machine_lambdas/requirements.txt \
-t lambda-functions/state_machine_lambdas \
--upgrade

sam build

echo "Deploying the bootstrap bucket stack."
source $SCRIPT_DIR/deploy-bootstrap-bucket-stack.sh

echo "Deploying the Terraform CLI wrapper scripts"
cd wrapper-scripts
python3 setup.py bdist_wheel
aws s3 sync dist s3://$BOOTSTRAP_BUCKET_NAME/dist --region $AWS_REGION

cd .. # project root dir

echo "Checking to see if this is a new installation or an update to an existingg installation."
STACK_EXISTS_CHECK=`aws cloudformation describe-stacks --stack-name $SAM_STACK_NAME --region $AWS_REGION 2>&1 || true`
if [[ "$STACK_EXISTS_CHECK" =~ "does not exist" ]]
then 
  echo "First-time installation. Deploying the Terraform reference engine stack with name: $SAM_STACK_NAME"
  SAM_STACK_EXISTS=1
else
  echo "Verifying describe-stacks command output:"
  echo "$STACK_EXISTS_CHECK"
  echo $STACK_EXISTS_CHECK | jq . > /dev/null
  echo "Updating existing installation. Deploying the Terraform reference engine stack with name: $SAM_STACK_NAME"
  SAM_STACK_EXISTS=0
fi

# Set up parameter overrides for sam deploy, if any are needed
SERVICE_CATALOG_PARAMETER_OVERRIDES="$OVERRIDE_SERVICE_CATALOG_ENDPOINT $OVERRIDE_SERVICE_CATALOG_VERIFY_SSL"
if [[ $SERVICE_CATALOG_PARAMETER_OVERRIDES =~ [A-Za-z] ]]
then
  SAM_DEPLOY_PARAMETER_OVERRIDES="--parameter-overrides $SERVICE_CATALOG_PARAMETER_OVERRIDES"
else
  unset SAM_DEPLOY_PARAMETER_OVERRIDES
fi

echo "Sending output of the sam deploy command to $SAM_DEPLOY_OUTPUT. This is done to check the results after the command has completed."
echo "This may take a while. Please be patient."
sam deploy --s3-bucket $BOOTSTRAP_BUCKET_NAME \
--stack-name $SAM_STACK_NAME --capabilities CAPABILITY_NAMED_IAM --region $AWS_REGION $SAM_DEPLOY_PARAMETER_OVERRIDES > $SAM_DEPLOY_OUTPUT 2>&1 || true

if [[ `grep "Successfully created/updated stack" $SAM_DEPLOY_OUTPUT` || `grep "Error: No changes to deploy" $SAM_DEPLOY_OUTPUT` ]]
then
  echo "Deployment succeeded"
else
  echo "Deployment failed. Check $SAM_DEPLOY_OUTPUT for details."
  echo "Deactivating python virtual environment"
  exit 1
fi

# Safely replace the EC2 instances if this is an update to an existing environment
if (( $SAM_STACK_EXISTS == 0 ))
then
  echo "Now safely replacing EC2 instances."
  pip3 install boto3 --upgrade
  export AWS_REGION
  python3 $SCRIPT_DIR/replace-ec2-instances.py
fi

echo "Deactivating python virtual environment"
deactivate

echo "Deployment finished successfully for account $AWS_ACCOUNT_ID in $AWS_REGION. The script took $SECONDS seconds."

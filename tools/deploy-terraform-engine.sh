#!/usr/bin/env bash

# shellcheck disable=SC2046

set -o errexit
set -o errtrace
set -o pipefail
set -o allexport


# =======================================================================================
#                           Constants and Global Configuration
# =======================================================================================
VERSION=v1.0.0
PROJECT_ROOT_DIR=$(git rev-parse --show-toplevel)
BOOTSTRAP_BUCKET_PREFIX="terraform-engine-bootstrap"
DEFAULT_BOOTSTRAP_STACK_NAME="Bootstrap-TRE"
DEFAULT_BOOTSTRAP_TEMPLATE="${PROJECT_ROOT_DIR}/cfn-templates/Bootstrap.yaml"
DEFAULT_STACK_NAME="SAM-TRE"
DEFAULT_STACK_TEMPLATE="${PROJECT_ROOT_DIR}/.aws-sam/packaged.yaml"
OUTPUT_SEPARATOR="============================================================"
REQUIRED_PYTHON_VERSION=3.7.16


# ====================================================================
#                           Library Imports
# ====================================================================
. "${PROJECT_ROOT_DIR}/tools/lib/base-lib.sh"
. "${PROJECT_ROOT_DIR}/tools/lib/aws-lib.sh"
. "${PROJECT_ROOT_DIR}/tools/lib/python-lib.sh"


# ==========================================================================
#                           Arguments and Options
# ==========================================================================
display_usage() {
  echo "Deploys the Terraform Reference Engine (TRE) to an AWS environment."
  echo ""
  echo "Usage:"
  echo "  deploy-terraform-engine.sh [--region <region>]"
  echo ""
  echo "Options:"
  echo "  --region <region>"
  echo -e "${TAB}The AWS region where the TRE should be deployed."
  echo -e "${TAB}If unspecified, the script attempts to use values set in either the"
  echo -e "${TAB}AWS_DEFAULT_REGION or AWS_REGION environment variables."
  echo ""
  echo "  --bootstrap-stack-name <bootstrap_stack_name>"
  echo -e "${TAB}The name assigned to the bootstrap TRE CloudFormation stack."
  echo -e "${TAB}Defaults to '${DEFAULT_BOOTSTRAP_STACK_NAME}'."
  echo ""
  echo "  --bootstrap-template <bootstrap_template>"
  echo -e "${TAB}The CloudFormation template file used to create bootstrap resources."
  echo -e "${TAB}Defaults to '(PROJECT_ROOT_DIR)/cfn-templates/Bootstrap.yaml'."
  echo ""
  echo "  --stack-name <main_stack_name>"
  echo -e "${TAB}The name assigned to the main TRE CloudFormation stack."
  echo -e "${TAB}Defaults to '${DEFAULT_STACK_NAME}'."
  echo ""
  echo "  --stack-template <stack_template>"
  echo -e "${TAB}The CloudFormation template file used to create TRE resources."
  echo -e "${TAB}Defaults to '(PROJECT_ROOT_DIR)/template.yaml'."
  echo ""
  echo "  --version"
  echo -e "${TAB}Shows the version of this tool."
  echo ""
  echo "  -h, --help"
  echo -e "${TAB}Shows this help message."
}

display_version() {
  echo "deploy-terraform-engine.sh ${VERSION} $(lower $(uname))/$(uname -m)"
}

while [ $# -gt 0 ]; do
  case "$1" in
    # The AWS region where the Terraform Reference Engine should be deployed.
    --region)
      shift
      check_option_value "--region" "${1}" || {
        display_usage && exit $(false)
      }
      REGION_ARG="${1}" ;;

    # The name assigned to the bootstrap TRE CloudFormation stack.
    --bootstrap-stack-name)
      shift
      check_option_value "--bootstrap-stack-name" "${1}" || {
        display_usage && exit $(false)
      }
      BOOTSTRAP_STACK_NAME_ARG="${1}" ;;

    # The CloudFormation template file used to create bootstrap resources.
    --bootstrap-template)
      shift
      check_option_value "--bootstrap-template" "${1}" "True" || {
        display_usage && exit $(false)
      }
      BOOTSTRAP_TEMPLATE_ARG="${1}" ;;

    # The name assigned to the main TRE CloudFormation stack.
    --stack-name)
      shift
      check_option_value "--stack-name" "${1}" || {
        display_usage && exit $(false)
      }
      STACK_NAME_ARG="${1}" ;;

    # The CloudFormation template file used to create bootstrap resources.
    --stack-template)
      shift
      check_option_value "--stack-template" "${1}" "True" || {
        display_usage && exit $(false)
      }
      STACK_TEMPLATE_ARG="${1}" ;;

    # Display usage information.
    --version)
      display_version && exit $(true) ;;

    # Display usage information.
    -h|--help)
      display_usage && exit $(true) ;;

    *)
      log_error "Invalid option specified"
      display_usage && exit $(false) ;;
  esac
  shift
done


# ========================================================================
#                           Prerequisite Checks
# ========================================================================

# Check if a Python virtual environment exists within the project root and create
# a new virtual environment if not, exiting on failure.
create_python_virtualenv || exit $(false)

# Check if we are running in the virtual environment within the project root and
# attempt to activate it if not, exiting on failure.
activate_python_virtualenv || exit $(false)

# Verify the version of Python running in the virtual environment meets or exceeds
# the minimum required version defined in `REQUIRED_PYTHON_VERSION`.
check_python_version "${REQUIRED_PYTHON_VERSION}" || exit $(false)

# Verify all Python packages specified in the requirements.txt file are installed
# in the virtual environment and install them if not, exiting on failure.
install_python_requirements || exit $(false)


# ==============================================================================
#                           Bootstrap TRE Environment
# ==============================================================================

# Retrieve the AWS region and account in which we are deploying the Terraform
# Reference Engine, exiting on failure.
region=$(get_aws_region "${REGION_ARG}")
account_id=$(get_aws_account_id "${region}")

# Check if the TRE bootstrap stack exists and create it if not, exiting on
# failure.
bootstrap_stack="${BOOTSTRAP_STACK_NAME_ARG:-${DEFAULT_BOOTSTRAP_STACK_NAME}}"
bootstrap_template="${BOOTSTRAP_TEMPLATE_ARG:-${DEFAULT_BOOTSTRAP_TEMPLATE}}"
create_cloudformation_stack \
  "${bootstrap_stack}" \
  "${bootstrap_template}" \
  "${region}" || exit $(false)

# Verify the bootstrap S3 bucket exists before initiating build operation
# for the Terraform Runner package, exiting on failure.
bootstrap_bucket="${BOOTSTRAP_BUCKET_PREFIX}-${account_id}-${region}"
check_bucket_exists "${bootstrap_bucket}" "${region}" || exit $(false)

# Execute a local build operation for the Terraform Runner package,
# exiting on failure.
log_info "Initiating a local build operation for the Terraform Runner `
  `package and deploying to S3 bucket ${bootstrap_bucket}\n\n${OUTPUT_SEPARATOR}"
execute_makefile_target \
  "build-terraform-runner" \
  "${region}" \
  ""|| exit $(false)

# Execute a containerized build operation for the TRE Lambda functions
# using AWS SAM CLI, exiting on failure.
echo -e "${OUTPUT_SEPARATOR}"
log_info "Initiating a containerized build operation for the Terraform `
  `Reference Engine Lambda functions\n\n${OUTPUT_SEPARATOR}"
execute_makefile_target "build-lambda-functions" "${region}" || exit $(false)
echo -e "${OUTPUT_SEPARATOR}"

primary_stack="${STACK_NAME_ARG:-${DEFAULT_STACK_NAME}}"
primary_stack_template="${STACK_TEMPLATE_ARG:-${DEFAULT_STACK_TEMPLATE}}"
if cloudformation_stack_exists "${primary_stack}" "${region}"; then
  # Safely stop the existing Terraform Reference Engine to quiesce any
  # actively running tasks, pause processing of new requests, and
  # terminate TRE execution instances.
  log_info "The Terraform Reference Engine has already been deployed in AWS `
    `account ${account_id} and region ${region}, gracefully stopping the `
    `existing TRE environment"
  execute_tre_action "stop" "${region}" || exit $(false)

  # Deploy any required updates to the existing Terraform Reference Engine
  # environment using the AWS SAM CLI, exiting on failure.
  deploy_sam_stack \
    "${primary_stack}" \
    "${primary_stack_template}" \
    "${bootstrap_bucket}" \
    "${region}" || exit $(false)

  # Resume processing of new requests in the deployed Terraform Reference
  # Engine environment.
  log_info "Configuring the Terraform Reference Engine environment in AWS `
    `account ${account_id} and region ${region} to resume processing of `
    `new requests"
  execute_tre_action "start" "${region}" || exit $(false)
else
  log_info "Deploying the Terraform Reference Engine for the first time in `
    `AWS account ${account_id} and region ${region}"

  deploy_sam_stack \
    "${primary_stack}" \
    "${primary_stack_template}" \
    "${bootstrap_bucket}" \
    "${region}" || exit $(false)
fi

log_info "The Terraform Reference Engine has been successfully deployed to `
  `AWS account ${account_id} and region ${region}"

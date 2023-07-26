#!/usr/bin/env bash

# shellcheck disable=SC2046

# ===============================================================================
#                       Constants and Global Configuration
# ===============================================================================
PROJECT_ROOT_DIR=$(git rev-parse --show-toplevel)
DEFAULT_LOG_DIR="${PROJECT_ROOT_DIR}/.aws-sam/logs"
DEFAULT_VIRTUALENV_PATH="${PROJECT_ROOT_DIR}/venv"


# ========================================================================
#                             Library Imports
# ========================================================================
. "${PROJECT_ROOT_DIR}/tools/lib/base-lib.sh"


# ==============================================================
#                       AWS CLI Functions
# ==============================================================
get_aws_cli_version() {
  check_prerequisite_installed "aws" || {
    log_error "Unable to get AWS CLI version: no AWS CLI binary was found `
      `on your local system"
    return $(false)
  }
  local -r aws_cli_version=$(
    /usr/bin/env aws --version | awk '{print $1}' | tr -d "aws-cli/"
  )
  echo "${aws_cli_version}"
}

check_aws_cli_response() {
  if echo "$1" | python3 -c \
    "import sys, json; json.load(sys.stdin)" > /dev/null 2>&1; then
      return $(true)
  fi
  return $(false)
}



# ==================================================================
#                       General AWS Functions
# ==================================================================
aws_region_is_valid() {
  local region="${1:-${AWS_REGION}}"
  local virtualenv_path="${2:-${DEFAULT_VIRTUALENV_PATH}}"
  local -r python_exec="${virtualenv_path}/bin/python3"
  local aws_region_list
  local valid_aws_regions=()

  # Obtain a list of valid AWS regions from the AWS Python SDK and
  # convert the returned Python list to a string array.
  # shellcheck disable=SC2155
  local aws_region_list=$(
    "${python_exec}" -c \
      "from boto3.session import Session; print(Session().get_available_regions('sts'))"
  )
  while read -r aws_region; do
    valid_aws_regions+=("${aws_region}")
  done < <(echo "${aws_region_list}" | tr -d '[],' | xargs -n1)

  for aws_region in "${valid_aws_regions[@]}"; do
    [[ "${aws_region}" == $(lower "${region}") ]] && return $(true)
  done

  log_error "The specified AWS region ${region} is not a valid AWS region"

  return $(false)
}

get_aws_account_id() {
  local region="${1:-${AWS_REGION}}"

  account_id=$(
    /usr/bin/env aws sts get-caller-identity \
      --query "Account" \
      --region "${region}" \
      --output text 2>&1
  )

  [[ -z "${account_id}" || ! "${account_id}" =~ ^[0-9]{12}$ ]] && {
    log_error "Unable to determine the AWS account ID: ${account_id}"
    exit $(false)
  }

  echo "${account_id}"
}

get_aws_region() {
  local region="${1:-${AWS_REGION}}"
  local exit_on_failure="${2:-True}"

  [[ -z "${region}" ]] && {
    region="${AWS_DEFAULT_REGION:-${region}}"
    region="${AWS_PROFILE_REGION:-${region}}"
    region="${AWS_REGION:-${region}}"
  }

  [[ -z "${region}" && "${exit_on_failure}" == "True" ]] && {
    log_error "No AWS region specified and unable to automatically `
      `determine the correct AWS region"
    exit $(false)
  }

  aws_region_is_valid "${region}" || exit $(false)

  echo "${region}"
}


# =========================================================================
#                       AWS CloudFormation Functions
# =========================================================================
check_cloudformation_stack_state() {
  local stack_name="${1}"
  local region="${2:-${AWS_REGION}}"
  local desired_state="${3:-}"

  local attempts=0
  local -r max_attempts=10
  local -r wait_interval=15

  [[ -z "${desired_state}" ]] && {
    desired_state="CREATE_COMPLETE|UPDATE_COMPLETE"
  }

  log_info "Waiting for AWS CloudFormation stack ${stack_name} to reach the `
    `desired state ${desired_state}"

  while true; do
    attempts=$((attempts+1))
    stack_state=$(get_cloudformation_stack_state "${stack_name}" "${region}")

    [[ $(lower "${stack_state}") =~ $(lower "${desired_state}") ]] && {
      log_info "The AWS CloudFormation stack ${stack_name} has successfully `
        `reached the desired state ${desired_state}"
      return $(true)
    }

    [ "${attempts}" -ge "${max_attempts}" ] && {
      log_warning "The AWS CloudFormation stack ${stack_name} has not reached `
        `the desired state ${desired_state} and the maximum number of retries `
        `has been reached (${attempts}/${max_attempts})"
      break
    }

    log_debug "The AWS CloudFormation stack ${stack_name} has not reached the `
      `desired state ${desired_state}, retrying in ${wait_interval} seconds"
    sleep "${wait_interval}"
  done

  return $(false)
}

cloudformation_stack_exists() {
  local stack_name="${1}"
  local region="${2:-${AWS_REGION}}"

  log_debug "Checking if AWS CloudFormation stack ${stack_name} exists in `
    `region ${region}"

  stack_data=$(
    aws cloudformation describe-stacks \
      --stack-name "${stack_name}" \
      --region "${region}" 2>/dev/null
  )

  [[ -z "${stack_data}" ]] && {
    log_debug "The specified AWS CloudFormation stack ${stack_name} does `
      `not exist in region ${region}"
    return $(false)
  }

  log_debug "The specified AWS CloudFormation stack ${stack_name} exists `
    `in region ${region}"

  return $(true)
}

create_cloudformation_stack() {
  local stack_name="${1}"
  local template_file="${2}"
  local region="${3:-${AWS_REGION}}"
  local stack_exists="False"

  [[ -f "${template_file}" ]] || {
    log_error "Unable to create CloudFormation Stack: no CloudFormation `
      `template file found at path ${template_file}"
    return $(false)
  }

  if cloudformation_stack_exists "${stack_name}" "${region}"; then
    log_info "The specified CloudFormation Stack ${stack_name} already `
      `exists in region ${region}, checking for required updates"
    stack_exists="True"
    stack_operation_response=$(
      aws cloudformation update-stack \
        --stack-name "${stack_name}" \
        --region "${region}" \
        --capabilities CAPABILITY_NAMED_IAM \
        --template-body "file://${template_file}" 2>&1
    )
    [[ "${stack_operation_response}" =~ "No updates are to be performed" ]] && {
      log_info "The specified CloudFormation Stack ${stack_name} in region `
        `${region} is up to date, no changes required"
      return $(true)
    }
  else
    log_info "Creating a new CloudFormation Stack named ${stack_name} `
      `in region ${region}"
    stack_operation_response=$(
      aws cloudformation create-stack \
        --stack-name "${stack_name}" \
        --region "${region}" \
        --capabilities CAPABILITY_NAMED_IAM \
        --template-body "file://${template_file}" 2>&1
    )
  fi

  check_aws_cli_response "${stack_operation_response}" || {
    log_error "An error occurred while attempting to create or update the `
      `CloudFormation Stack ${stack_name} in region ${region}: `
      `${stack_operation_response}"
    return $(false)
  }

  check_cloudformation_stack_state "${stack_name}" "${region}" || {
    log_error "The CloudFormation Stack ${stack_name} in region ${region} `
      `never reached the ${desired_state} state"
    return $(false)
  }

  if [[ "${stack_exists}" == "True" ]]; then
    log_info "Successfully updated the specified CloudFormation Stack `
      `${stack_name} in region ${region}"
    return $(true)
  fi

  log_info "Successfully created CloudFormation Stack ${stack_name} in `
      `region ${region}"
  return $(true)
}

get_cloudformation_stack_state() {
  local stack_name="${1}"
  local region="${2:-${AWS_REGION}}"

  log_debug "Getting the current state of AWS CloudFormation stack `
    `${stack_name} in region ${region}"

  stack_state=$(
    aws cloudformation describe-stacks \
      --stack-name "${stack_name}" \
      --region "${region}" \
      --query "Stacks[0].StackStatus" \
      --output text 2>/dev/null
  )

  [[ -z "${stack_state}" ]] && {
    log_warning "The specified AWS CloudFormation stack ${stack_name} does `
      `not exist in region ${region}"
  }

  log_debug "The current state of AWS CloudFormation stack ${stack_name} is: `
    `${stack_state}"

  echo "${stack_state}"
}


# =============================================================
#                       AWS S3 Functions
# =============================================================
check_bucket_exists() {
  local bucket_name="${1}"
  local region="${2:-${AWS_REGION}}"
  region=$(lower "${region}")

  log_debug "Checking if the specified S3 bucket ${bucket_name} exists `
    `in region ${region}"

  aws s3api head-bucket --bucket "${bucket_name}" 2>/dev/null || {
    log_warning "The specified S3 bucket ${bucket_name} does not exist"
    return $(false)
  }

  bucket_region=$(lower \
    $(aws s3api get-bucket-location \
      --bucket "${bucket_name}" \
      --query "LocationConstraint" \
      --output text 2>/dev/null)
  )

  [[ "${bucket_region}" != "${region}" && "${bucket_region}" != "none" ]] && {
    log_warning "The specified S3 bucket ${bucket_name} exists in region `
      `${bucket_region} not in the expected region ${region}"
    return $(false)
  }

  log_debug "The specified S3 bucket ${bucket_name} exists in region ${region}"
  return $(true)
}

copy_directory_to_bucket() {
  local directory_path="${1}"
  local bucket_name="${2}"

  [[ -d "${directory_path}" ]] || {
    log_error "Unable to copy directory to S3 bucket: no directory found at `
      `path ${directory_path}"
    return $(false)
  }

  aws s3 cp \
    --recursive \
    "${directory_path}" \
    "s3://${bucket_name}/dist" > /dev/null 2>&1 || {
      log_error "An error occurred while attempting to copy the directory at `
        `path ${directory_path} to S3 bucket ${bucket_name}"
      return $(false)
    }

  log_debug "Successfully copied the directory at path ${directory_path} to S3 `
    `bucket ${bucket_name}"

  return $(true)
}


# ==================================================================
#                       AWS SAM CLI Functions
# ==================================================================
check_sam_response() {
  local sam_output_log="${1}"
  local stack_name="${2}"
  local sam_response

  [[ -r "${sam_output_log}" ]] || {
    log_error "Unable to check AWS SAM CLI response: no output log was `
      `found at path ${sam_output_log} or the log is not readable"
    return $(false)
  }

  sam_response=$(cat "${sam_output_log}")
  [[ -z "${sam_response}" ]] && {
    log_error "Unable to check AWS SAM CLI response: the output log at `
      `path ${sam_output_log} is empty"
    return $(false)
  }

  [[ "${sam_response}" =~ "Error: No changes to deploy" ]] && {
    log_info "The stack ${stack_name} is up to date, there are no `
      `changes to deploy"
    return $(true)
  }
  [[ "${sam_response}" =~ "Successfully created/updated stack" ]] && {
    log_info "The stack ${stack_name} was successfully deployed or `
      `updated"
    return $(true)
  }

  log_error "An error occurred while attempting to deploy or update `
    `the stack ${stack_name}, please review the output log at path `
    `${sam_output_log} for more information"
  return $(false)

}

deploy_sam_stack() {
  local stack_name="${1}"
  local template_file="${2}"
  local bucket_name="${3}"
  local region="${4:-${AWS_REGION}}"
  local virtualenv_path="${5:-${DEFAULT_VIRTUALENV_PATH}}"
  local -r sam_exec="${virtualenv_path}/bin/sam"

  [[ -d "${virtualenv_path}" ]] || {
    log_error "Unable to execute AWS SAM CLI deploy: no Python virtual `
      `environment was found at path ${virtualenv_path}"
    return $(false)
  }

  [[ -f "${sam_exec}" ]] || {
    log_error "Unable to execute AWS SAM CLI deploy: an AWS SAM CLI executable `
      `was not found at path ${sam_exec}"
    return $(false)
  }
  [[ -f "${template_file}" ]] || {
    log_error "Unable to execute AWS SAM CLI deploy: a template file was not `
      `found at path ${template_file}"
    return $(false)
  }

  log_info "Executing an AWS SAM CLI deploy of stack ${stack_name} in region `
    `${region} using template ${template_file}"

  # Get the current version of the Terraform Runner package and pass it to the
  # AWS SAM template.
  tf_runner_ver=$(
    awk '{print $3}' < "${PROJECT_ROOT_DIR}/wrapper-scripts/terraform_runner/__init__.py" | xargs
  )

  # Create the AWS SAM CLI output log directory if it does not exist, and
  # compute the correct output log file name.
  [[ -d "${DEFAULT_LOG_DIR}" ]] || mkdir -p "${DEFAULT_LOG_DIR}"
  local -r output_log="${DEFAULT_LOG_DIR}/aws-sam-output-$(utc_date true).log"

  ${sam_exec} deploy \
    --config-file "${PROJECT_ROOT_DIR}/samconfig.toml" \
    --config-env "default" \
    --region "${region}" \
    --s3-bucket "${bucket_name}" \
    --parameter-overrides "ParameterKey=TerraformRunnerVersion,ParameterValue=${tf_runner_ver}" \
    --template-file "${template_file}" > "${output_log}" 2>&1

  delete_old_logs "${DEFAULT_LOG_DIR}"
  check_sam_response "${output_log}" "${stack_name}" || return $(false)

  return $(true)
}
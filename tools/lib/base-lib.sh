#!/usr/bin/env bash

# shellcheck disable=SC2046


# ===============================================================================
#                       Constants and Global Configuration
# ===============================================================================
PROJECT_ROOT_DIR=$(git rev-parse --show-toplevel)
DEFAULT_LOG_DIR="${PROJECT_ROOT_DIR}/.aws-sam/logs"
DEFAULT_LOG_PATTERN="aws-sam-output*.log"

# shellcheck disable=SC2034
BLUE="\033[94m"
GRAY="\033[37m"
GREEN="\033[92m"
NC="\033[0m"
RED="\033[91m"
TAB="\t"
YELLOW="\033[93m"


# =====================================================================
#                       General Helper Functions
# =====================================================================
check_file_exists() {
  local file_path="${1}"
  local exit_on_error="${2:-True}"
  [[ -f "${file_path}" ]] || {
    log_error "The specified file ${file_path} does not exist"
    [[ $(lower "${exit_on_error}") == "true" ]] && exit $(false)
    return $(false)
  }
  echo "${file_path}" | sed 's/\/*$//g'
}

check_option_value() {
  local option_name="${1}"
  local option_value="${2}"
  local is_file="${3:-False}"

  [[ -z "${option_value}" ]] && {
    log_error "The option [${option_name}] requires an argument, but none `
      `was received"
    return $(false)
  }

  [[ "${option_value}" == -* ]] && {
    log_error "The option [${option_name}] requires an argument, but the `
      `argument received appears to be invalid: ${option_value}"
    return $(false)
  }

  [[ $(lower "${is_file}") == "true" && ! -f "${option_value}" ]] && {
    log_error "The option [${option_name}] requires a valid file, but the `
      `file specified in the argument does not exist: ${option_value}"
    return $(false)
  }

  return $(true)
}

check_if_retryable() {
  local attempt="${1}"
  local max_attempts="${2:-5}"
  local wait_interval="${3:-30}"

  [ "${attempt}" -ge "${max_attempts}" ] && {
    return $(false)
  }

  log_debug "Retrying in ${wait_interval} seconds (${attempt}/${max_attempts})"
  sleep "${wait_interval}"

  return $(true)
}

check_required_version(){
  local version="${1}"
  local required_version="${2}"
  local strict_mode="${3:-False}"

  [[ "${version}" == "${required_version}" ]] && return $(true)
  [[ $(lower "${strict_mode}") != "true" ]] && {
    local -r lowest_version="$(printf '%s\n' "${version}" "${required_version}" | sort -V | head -n1)"
    [[ "${lowest_version}" = "${required_version}" ]] && return $(true)
  }

  return $(false)
}

confirmation_prompt() {
  local message="${1}"

  echo -e "${RED}${message}${NC}"
  read -r confirmation_answer

  [[ $(lower "${confirmation_answer}") == "yes" ]] && return $(true)

  log_debug "The user did not provide an affirmative answer to the `
    `confirmation prompt"

  return $(false)
}

delete_old_logs() {
    local log_dir="${1:-${DEFAULT_LOG_DIR}}"
    local log_pattern="${2:-${DEFAULT_LOG_PATTERN}}"
    local retention_threshold="${3:-10}"

    [[ -d "${log_dir}" ]] || {
      log_warning "Unable to delete old logs: the specified directory `
        `at path ${log_dir} does not exist"
      return $(false)
    }

    # List files matching the specified pattern, sort by modification time,
    # and skip the n most recent, as defined in the retention_threshold,
    # delete the rest.
    find "${log_dir}" -type f -name "${log_pattern}" | \
      sort -r -n -t _ -k 2 | \
      awk -v keep_count="${retention_threshold}" 'NR > keep_count' | \
      xargs -I{} rm -f {}

    return $(true)
}

get_absolute_path() {
  local relative_path="${1}"
  echo "$(cd "$(dirname "${relative_path}")" && pwd)/$(basename "${relative_path}")"
}

# shellcheck disable=SC2120
utc_date() {
  local compressed="${1:-False}"
  if [[ $(lower "${compressed}") == "true" ]]; then
    date -u "+%Y%m%d%H%M%S"
  else
    date -u "+%Y-%m-%dT%H:%M:%SZ"
  fi
}


# ==========================================================================
#                       String Manipulation Functions
# ==========================================================================
convert_python_list_to_array() {
  local python_list="${1}"
  local string_array=()

  [[ -z "${python_list}" ]] && return $(false)

  while read -r list_item; do
    string_array+=("${list_item}")
  done < <(echo "${python_list}" | tr -d '[],' | xargs -n1)

  echo "${string_array[@]}"
}

lower() {
  local input_string="${1:-}"
  if [[ -n "${input_string}" ]]; then
    echo "${input_string}" | tr '[:upper:]' '[:lower:]'
  else
    echo "${input_string}"
  fi
}


# ==============================================================
#                       Logging Functions
# ==============================================================
log_debug() {
  local message="${1}"
  [[ $(lower "${LOG_LEVEL}") == "debug" ]] && {
    echo -e "$(utc_date) [DEBUG] - ${message}" > /dev/stderr
  }
}

log_error() {
  local message="${1}"
  local exit_on_error="${2:-False}"
  echo -e "$(utc_date) ${RED}[ERROR] - ${message}${NC}" \
    > /dev/stderr
  [[ $(lower "${exit_on_error}") == "true" ]] && exit $(false)
}

log_info() {
  local message="${1}"
  echo -e "$(utc_date) [INFO] - ${message}" > /dev/stderr
}

log_warning() {
  local message="${1}"
  echo -e "$(utc_date) ${YELLOW}[WARNING] - ${message}${NC}" \
    > /dev/stderr
}



# ===========================================================================
#                       General Prerequisite Functions
# ===========================================================================
check_docker_engine() {
  check_prerequisite_installed "docker" || return $(false)

  if ! /usr/bin/env docker info > /dev/null 2>&1; then
    log_warning "The Docker Engine is not running on your system, please `
      `start the Docker Engine and try again"
    return $(false)
  fi

  log_debug "Successfully confirmed the Docker Engine is running on your system"

  return $(true)
}

check_prerequisite_installed() {
  local prerequisite_name="${1}"
  local prerequisite_path="${2:-}"
  local exit_on_error="${3:-False}"

  log_debug "Checking if the prerequisite binary ${prerequisite_name} is `
    `installed on your local system"

  local -r binary_path=$(command -v "${prerequisite_name}")
  [[ -z "${binary_path}" ]] && {
    log_error "The prerequisite binary ${prerequisite_name} is not installed on `
      `your local system" "${exit_on_error}"
    return $(false)
  }

  [[ -n "${prerequisite_path}" ]] && {
    [[ "${binary_path}" != "${prerequisite_path}" ]] && {
      log_error "The prerequisite binary was discovered at path ${binary_path} `
        `but does not match the required path ${prerequisite_path}" \
        "${exit_on_error}"
      return $(false)
    }
  }

  log_debug "The prerequisite binary ${prerequisite_name} was successfully `
    `discovered on your local system at path ${binary_path}"

  return $(true)
}



# ==========================================================================
#                         Build Operation Functions
# ==========================================================================
execute_makefile_target() {
  local makefile_target="${1:-build}"
  local region="${2:-${AWS_REGION}}"
  local makefile_path="${3:-${PROJECT_ROOT_DIR}/Makefile}"

  [[ -z "${makefile_target}" ]] && {
    log_error "Unable to execute makefile target: no target was specified"
    return $(false)
  }

  [[ -f "${makefile_path}" ]] || {
    log_error "Unable to execute makefile target: no makefile was found at `
      `path: ${makefile_path}"
    return $(false)
  }

  log_debug "Executing the ${makefile_target} target in the makefile at `
    `path ${makefile_path}"
  check_prerequisite_installed "make" || return $(false)

  AWS_REGION="${region}" make \
    --makefile "${makefile_path}" \
    --warn-undefined-variables \
    "${makefile_target}" || {
      log_error "An error occurred while attempting to execute the `
        `${makefile_target} target in makefile at path ${makefile_path}"
      return $(false)
    }

  return $(true)
}


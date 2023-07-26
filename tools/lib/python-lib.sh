#!/usr/bin/env bash

# shellcheck disable=SC2046


# ===============================================================================
#                       Constants and Global Configuration
# ===============================================================================
MINIMUM_REQUIRED_PIP_VERSION="23.2"
PROJECT_ROOT_DIR=$(git rev-parse --show-toplevel)
DEFAULT_TRE_ACTION="status"
DEFAULT_VIRTUALENV_PATH="${PROJECT_ROOT_DIR}/.venv"
TOOLS_DIR="${PROJECT_ROOT_DIR}/tools"


# ========================================================================
#                             Library Imports
# ========================================================================
. "${PROJECT_ROOT_DIR}/tools/lib/base-lib.sh"


# =====================================================================
#                       General Python Functions
# =====================================================================
check_pip_version() {
  local virtualenv_path="${1:-${DEFAULT_VIRTUALENV_PATH}}"
  local req_version="${2:-${MINIMUM_REQUIRED_PIP_VERSION}}"

  [[ -z "${req_version}" ]] && {
    log_error "Unable to check pip version: no required version was specified"
    return $(false)
  }

  local -r pip_exec="${virtualenv_path}/bin/pip3"
  local -r version=$(get_pip_version "${virtualenv_path}")

  check_required_version "${version}" "${req_version}" || {
    log_warning "The pip binary at path ${pip_exec} is running version `
      `${version} which does not satisfy the minimum required version `
      `${req_version}"
    return $(false)
  }

  log_debug "The pip binary at path ${pip_exec} is running version ${version} `
    `which meets or exceeds the minimum required version ${req_version}"
  return $(true)
}

check_python_version() {
  local req_version="${1}"
  local virtualenv_path="${2:-${DEFAULT_VIRTUALENV_PATH}}"

  [[ -z "${req_version}" ]] && {
    log_error "Unable to check Python version: no required version was specified"
    return $(false)
  }

  local -r python_exec="${virtualenv_path}/bin/python3"
  local -r version=$(get_python_version "${virtualenv_path}")

  check_required_version "${version}" "${req_version}" || {
    log_warning "The Python binary at path ${python_exec} is running version `
      `${version} which does not satisfy the required version ${req_version}"
    return $(false)
  }

  log_debug "The Python binary at path ${python_exec} is running version `
    `${version} which meets or exceeds the required version ${req_version}"
  return $(true)
}

execute_tre_action() {
  local action="${1:-${DEFAULT_TRE_ACTION}}"
  local region="${2:-${AWS_REGION}}"
  local virtualenv_path="${3:-${DEFAULT_VIRTUALENV_PATH}}"
  local -r python_exec="${virtualenv_path}/bin/python3"

  [[ -d "${virtualenv_path}" ]] || {
    log_error "Unable to execute TRE action: no Python virtual environment `
      `was found at path ${virtualenv_path}"
    return $(false)
  }

  [[ -f "${python_exec}" ]] || {
    log_error "Unable to execute TRE action: a Python executable was not `
      `found at path ${python_exec}"
    return $(false)
  }

  log_debug "Executing the ${action} action against the existing Terraform `
    `Reference Engine environment"

  ${python_exec} "${TOOLS_DIR}/manage-terraform-engine.py" \
    --auto-approve \
    --region "${region}" \
    --action "${action}" || {
      log_error "An error occurred while attempting to execute the ${action} `
        `action against the existing Terraform Reference Engine environment"
      return $(false)
    }

  return $(true)
}

get_pip_version() {
  local virtualenv_path="${1:-${DEFAULT_VIRTUALENV_PATH}}"
  local -r python_exec="${virtualenv_path}/bin/python3"

  [[ -d "${virtualenv_path}" ]] || {
    log_error "Unable to get pip version: no Python virtual environment `
      `was found at path ${virtualenv_path}"
    return $(false)
  }

  [[ -f "${python_exec}" ]] || {
    log_error "Unable to get pip version: a Python executable was not `
      `found at path ${python_exec}"
    return $(false)
  }

  local -r pip_version=$(
    ${python_exec} -m pip --version 2>&1 | awk '{print $2}'
  )
  echo "${pip_version}"
}

get_python_version() {
  local virtualenv_path="${1:-${DEFAULT_VIRTUALENV_PATH}}"
  local -r python_exec="${virtualenv_path}/bin/python3"

  [[ -d "${virtualenv_path}" ]] || {
    log_error "Unable to get Python version: no Python virtual environment `
      `was found at path ${virtualenv_path}"
    return $(false)
  }

  [[ -f "${python_exec}" ]] || {
    log_error "Unable to get Python version: a Python executable was not `
      `found at path ${python_exec}"
    return $(false)
  }

  local -r python_version=$(
    "${python_exec}" --version 2>&1 | awk '{print $2}' | tr -d "Python"
  )
  echo "${python_version}"
}

upgrade_pip_version() {
  local virtualenv_path="${1:-${DEFAULT_VIRTUALENV_PATH}}"
  local -r python_exec="${virtualenv_path}/bin/python3"
  local -r pip_exec="${virtualenv_path}/bin/pip3"

  [[ -f "${python_exec}" ]] || {
    log_error "Unable to upgrade pip to the latest version: a Python binary was `
      `not found at path ${python_exec}"
    return $(false)
  }

  previous_version=$(get_pip_version "${virtualenv_path}")
  ${python_exec} -m pip install \
    --upgrade \
    --quiet pip > /dev/null 2>&1 || {
      log_error "An error occurred while attempting to upgrade the version of `
        `pip at path ${pip_exec} to the latest version"
      return $(false)
    }

  current_version=$(get_pip_version "${virtualenv_path}")
  [[ "${previous_version}" == "${current_version}" ]] || {
    log_info "Successfully updated pip at path ${pip_exec} from version `
      `${previous_version} to ${current_version}"
    return $(true)
  }

  log_debug "The current version of pip ${current_version} at path `
      `${virtualenv_path} is already the latest available version"
  return $(true)
}


# ================================================================================
#                       Python Package Management Functions
# ================================================================================
check_python_requirements() {
  local requirements_file=${1:-"${TOOLS_DIR}/requirements.txt"}
  local virtualenv_path=${2:-"${DEFAULT_VIRTUALENV_PATH}"}
  local target_path=${3:-""}

  local -r python_exec="${virtualenv_path}/bin/python3"
  local -r pip_exec="${virtualenv_path}/bin/pip3"

  [[ -f "${requirements_file}" ]] || {
    log_error "Unable to check installation status of Python packages: no `
      `requirements file was found at path ${requirements_file}"
    return $(false)
  }

  [[ -f "${python_exec}" ]] || {
    log_error "Unable to check installation status of Python packages: no `
      `Python binary was found at path ${python_exec}"
    return $(false)
  }

  # If the caller passed a target path, skip the check as pip will always
  # indicate that installation is required in this case.
  [[ -z "${target_path}" ]] || {
    return $(false)
  }

  log_debug "Checking if all Python packages specified in the requirements file `
    `at path ${requirements_file} are installed on your local system"

  check_pip_version "${virtualenv_path}" || {
    log_debug "Upgrading the pip binary at path ${pip_exec} to a version that `
      `meets or exceeds the minimum required version ${MINIMUM_REQUIRED_PIP_VERSION}"
    upgrade_pip_version "${virtualenv_path}" || return $(false)
  }

  missing_packages=$(
    ${python_exec} -m pip install \
      --requirement "${requirements_file}" \
      --require-virtualenv \
      --disable-pip-version-check \
      --quiet \
      --quiet \
      --dry-run \
      --upgrade \
      --report - | ${python_exec} -c "import sys, json; print(len([pkg['metadata']['name'] for pkg in json.load(sys.stdin)['install']]))"
  )

  [ "${missing_packages}" -gt 0 ] && {
    log_warning "${missing_packages} of the Python packages specified in the `
      `requirements file at path ${requirements_file} are missing from your `
      `local system"
    return $(false)
  }

  log_debug "All Python packages specified in the requirements file at path `
    `${requirements_file} are installed on your local system"
  return $(true)
}

install_python_requirements() {
  local requirements_file="${1:-${TOOLS_DIR}/requirements.txt}"
  local virtualenv_path="${2:-${DEFAULT_VIRTUALENV_PATH}}"
  local target_path="${3:-}"

  local -r python_exec="${virtualenv_path}/bin/python3"

  [[ -f "${requirements_file}" ]] || {
    log_error "Unable to install Python packages: a requirements file was `
      `not found at path ${requirements_file}"
    return $(false)
  }

  check_python_requirements "${requirements_file}" "${virtualenv_path}" \
    "${target_path}" && return $(true)

  if [[ -n "${target_path}" ]]; then
    log_debug "Installing all Python packages specified in the requirements `
      `file at path ${requirements_file} to path ${target_path}"

    ${python_exec} -m pip install \
      --requirement "${requirements_file}" \
      --target "${target_path}" \
      --quiet \
      --quiet \
      --upgrade || {
        log_error "An unexpected error occurred while attempting to install the `
          `Python packages defined in the requirements file at path `
          `${requirements_file} on your local system at path ${target_path}"
        return $(false)
      }

    log_info "All Python packages specified in the requirements file at path `
      `${requirements_file} were installed successfully on your local system `
      `to path ${target_path}"
    return $(true)
  fi

  log_debug "Installing all Python packages specified in the requirements `
    `file at path ${requirements_file}"

  ${python_exec} -m pip install \
    --requirement "${requirements_file}" \
    --require-virtualenv \
    --quiet \
    --quiet \
    --upgrade || {
      log_error "An unexpected error occurred while attempting to install the `
        `Python packages defined in the requirements file at path `
        `${requirements_file} on your local system"
      return $(false)
    }

  log_info "All Python packages specified in the requirements file at path `
    `${requirements_file} were successfully installed on your local system"
  return $(true)
}


# ==========================================================================
#                       Virtual Environment Functions
# ==========================================================================
activate_python_virtualenv() {
  local virtualenv_path="${1:-${DEFAULT_VIRTUALENV_PATH}}"
  local -r activation_script="${virtualenv_path}/bin/activate"

  python_virtualenv_activated "${virtualenv_path}" && {
    return $(true)
  }

  log_info "Activating Python virtual environment at path ${virtualenv_path}"

  [[ -f "${activation_script}" ]] || {
    log_error "Unable to activate the Python virtual environment: no activation `
      `script found at ${activation_script}"
    return $(false)
  }

  # shellcheck source=.venv/bin/activate
  . "${activation_script}"

  python_virtualenv_activated "${virtualenv_path}" || {
    log_error "An error occurred while activating the specified Python virtual `
      `environment at path ${virtualenv_path}"
    return $(false)
  }

  return $(true)
}

create_python_virtualenv() {
  local virtualenv_path="${1:-${DEFAULT_VIRTUALENV_PATH}}"
  local overwrite_existing="${2:-False}"
  local -r python_exec="${virtualenv_path}/bin/python3"

  check_prerequisite_installed "python3" "" || return $(false)

  [[ -d "${virtualenv_path}" ]] && {
    [[ $(lower "${overwrite_existing}") != "true" ]] && return $(true)

    log_warning "An existing Python virtual environment was found at path `
        `${virtualenv_path} and you opted to overwrite"
    confirmation_prompt "Are you sure you want to overwrite the existing `
      `virtual environment at ${virtualenv_path}? (yes/no)" || return $(false)

    rm -rf "${virtualenv_path}"
  }

  log_info "Creating a new Python virtual environment at path ${virtualenv_path}"

  /usr/bin/env python3 -m venv "${virtualenv_path}" || {
    log_error "Failed to create a Python virtual environment at path `
      `${virtualenv_path}"
    return $(false)
  }

  [[ -f "${python_exec}" ]] || {
    log_error "Failed to created a Python virtual environment: Python executable `
      `not found at path ${python_exec}"
    return $(false)
  }

  local -r python_version=$(get_python_version "${virtualenv_path}")
  log_debug "Successfully created a new Python virtual environment at path `
    `${virtualenv_path}, running version ${python_version}"

  return $(true)
}

python_virtualenv_activated() {
  local virtualenv_path="${1:-${DEFAULT_VIRTUALENV_PATH}}"
  local -r python_exec="${VIRTUAL_ENV}/bin/python3"

  [[ -z "${VIRTUAL_ENV}" ]] && {
    log_debug "Python is not running in a virtual environment"
    return $(false)
  }

  [[ -f "${python_exec}" ]] || {
    log_debug "A Python virtual environment is set but no Python `
      `executable was found at path ${python_exec}"
    return $(false)
  }

  [[ "${VIRTUAL_ENV}" != "${virtualenv_path}" ]] && {
    log_debug "Python is running in a virtual environment at path `
      `${VIRTUAL_ENV} which does not match the required path `
      `${virtualenv_path}"
    return $(false)
  }

  local -r python_version=$(get_python_version "${VIRTUAL_ENV}")
  log_debug "Python is running in a virtual environment at path `
    `${python_exec}, running version ${python_version}"
  return $(true)
}


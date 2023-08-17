# ===============================================================================
# 							Global Environment Configuration
# ===============================================================================
PROJECT_ROOT_DIR := $(shell git rev-parse --show-toplevel)
VENV_DIR := $(PROJECT_ROOT_DIR)/.venv
TOOLS_DIR := $(PROJECT_ROOT_DIR)/tools
BIN := $(VENV_DIR)/bin
SHELL := /bin/bash
SYSTEM_PYTHON := $(or $(shell which python3), "/usr/bin/python3")



# ===============================================================================
# 							Dynamic Environment Configuration
# ===============================================================================
AWS_ACCOUNT_ID ?= $(shell aws sts get-caller-identity --output text --query Account 2>&1)
VALID_ACCOUNT_ID := $(shell echo $(AWS_ACCOUNT_ID) | egrep "^[0-9]{12}$$")
AWS_REGION := $(shell echo $${AWS_REGION:-$$AWS_DEFAULT_REGION})
AWS_REGION := $(or $(AWS_REGION), $(shell echo $${AWS_PROFILE_REGION}))
BOOTSTRAP_BUCKET ?= terraform-engine-bootstrap-$(AWS_ACCOUNT_ID)-$(AWS_REGION)



# ===============================================================================
# 						  		AWS SAM Configuration
# ===============================================================================
SAM_ROOT_DIR := $(PROJECT_ROOT_DIR)/.aws-sam
SAM_CONFIG_ENV ?= default
SAM_CONFIG_FILE ?= $(PROJECT_ROOT_DIR)/samconfig.toml
SAM_TEMPLATE_FILE ?= $(PROJECT_ROOT_DIR)/template.yaml
STACK_NAME ?= SAM-TRE


# ===============================================================================
# 						  	Terraform Runner Configuration
# ===============================================================================
TF_RUNNER_DIR := $(PROJECT_ROOT_DIR)/wrapper-scripts
TF_RUNNER_VER := $(shell head -n 1 $(TF_RUNNER_DIR)/terraform_runner/__init__.py | awk '{print $$3}' | xargs)
TF_RUNNER_DIST_FILE := terraform_runner-$(TF_RUNNER_VER)-py3-none-any.whl
TF_RUNNER_DIST_FILE_PATH := $(TF_RUNNER_DIR)/dist/$(TF_RUNNER_DIST_FILE)


# ===============================================================================
# 						  	Lambda Functions Configuration
# ===============================================================================
LAMBDA_FUNCTIONS_DIR := $(PROJECT_ROOT_DIR)/lambda-functions
OPS_HANDLER_DIR := $(LAMBDA_FUNCTIONS_DIR)/provisioning-operations-handler
PARAM_PARSER_DIR := $(LAMBDA_FUNCTIONS_DIR)/terraform_open_source_parameter_parser
STATE_MACHINE_DIR := $(LAMBDA_FUNCTIONS_DIR)/state_machine_lambdas



# ===============================================================================
#                           Global Shortcut Targets
# ===============================================================================
all: venv upgrade-pip test
build: build-terraform-runner build-lambda-functions
test: test-state-machine test-provisioning-handler test-tf-runner
.PHONY: all build build-lambda-functions build-terraform-runner check-docker check-prerequisites clean install-terraform-runner prerequisites test test-param-parser test-provisioning-handler test-tf-runner test-state-machine upgrade-pip venv


# ===============================================================================
#                           Global Convenience Targets
# ===============================================================================
help:
	@echo "venv    - create a virtualenv with all baseline dependencies installed"
	@echo "build   - package new code and build binary distributions of all local packages"
	@echo "clean   - remove build, test, coverage and Python artifacts locally"
	@echo "test    - run all unit tests for all local packages"

clean:
	@rm -rf .aws-sam/
	@rm -rf $(PARAM_PARSER_DIR)/bin
	@find . -type d -name 'dist' -exec rm -rf {} +
	@find . -type d -name '.venv' -exec rm -rf {} +
	@find . -type d -name '__pycache__' -exec rm -rf {} +
	@find . -type d -name '.eggs' -exec rm -rf {} +
	@find . -type d -name '*.egg-info' -exec rm -rf {} +
	@find . -type d -name "*.py[co]" -o -name .pytest_cache -exec rm -rf {} +
	@find . -name '*.egg' -exec rm -f {} +
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +
	@find . -name '*~' -exec rm -f {} +



# ========================================================================
#                           Prerequisite Checks
# ========================================================================
check-prerequisites: prerequisites check-docker
	@echo "AWS Account: $(AWS_ACCOUNT_ID)"
	@echo "AWS Region: $(AWS_REGION)"
	@echo "Directory Name: $(shell basename $(CURDIR))"
	@echo "All prerequisites are installed and configured properly."

PREREQS := aws python3
prerequisites:
	@for cmd in $(PREREQS); do \
		command -v $$cmd >/dev/null 2>&1 || \
		{ echo >&2 "$$cmd is required but it's not installed, aborting."; exit 1; }; \
	done

ifeq ($(VALID_ACCOUNT_ID),)
	$(error [ERROR] Unable to determine the ID of your AWS account, please ensure \
	your AWS credentials are valid and your profile is configured properly)
endif

ifeq ($(strip $(AWS_REGION)),)
	$(error [ERROR] Unable to determine the correct AWS region, please ensure your \
	 desired region is properly defined in your environment)
endif

check-docker:
	@command -v docker >/dev/null 2>&1 || \
	{ echo >&2 "[ERROR] Docker is required but it's not installed, aborting."; exit 1; }
	@docker version >/dev/null 2>&1 || \
	{ echo "[ERROR] Docker is required but the daemon is not running, please start it and try again."; exit 1; }

check-go:
	@command -v go >/dev/null 2>&1 || \
	{ echo >&2 "[ERROR] Go is required but it's not installed, aborting."; exit 1; }

check-stack-exists: prerequisites
	@test -n "$(STACK_NAME)"
	@$(info CloudFormation Stack Name: $(STACK_NAME))
	@aws cloudformation describe-stacks --stack-name $(STACK_NAME) > /dev/null 2>&1 && \
		(echo "Terraform Reference Engine is DEPLOYED in AWS account $(AWS_ACCOUNT_ID) and ` \
			`region $(AWS_REGION).") || \
		(echo "Terraform Reference Engine is NOT DEPLOYED in AWS account $(AWS_ACCOUNT_ID) and ` \
			`region $(AWS_REGION)."; exit 1)



# ===============================================================================
#                           Python Virtual Environment
# ===============================================================================
venv: prerequisites $(VENV_DIR)

$(VENV_DIR): $(TOOLS_DIR)/requirements.txt $(TF_RUNNER_DIR)/requirements.txt
	@$(SYSTEM_PYTHON) -m venv $(VENV_DIR)
	@$(BIN)/pip3 install --require-virtualenv --quiet --upgrade pip build setuptools
	@$(BIN)/pip3 install --require-virtualenv --requirement $(TOOLS_DIR)/requirements.txt
	@$(BIN)/pip3 install --require-virtualenv --requirement $(TF_RUNNER_DIR)/requirements.txt
	@$(BIN)/pip3 install --require-virtualenv --editable $(TF_RUNNER_DIR)
	@touch $(VENV_DIR)

upgrade-pip: venv
	@$(BIN)/pip3 install --require-virtualenv --quiet --upgrade pip



# ========================================================================
#                          Terraform Runner Targets
# ========================================================================
build-terraform-runner: upgrade-pip test-tf-runner
	@if [ -d "$(TF_RUNNER_DIR)/dist" ]; then rm -rf "$(TF_RUNNER_DIR)/dist"; fi
	@$(BIN)/pip3 install --require-virtualenv --quiet --upgrade build setuptools
	@$(BIN)/python3 -m build $(TF_RUNNER_DIR)
	@if [ ! -e $(TF_RUNNER_DIST_FILE_PATH) ]; then \
  	   echo "[ERROR] Build failed: no distribution binary found at path ` \
  	   `$(TF_RUNNER_DIST_FILE_PATH)." \
  	   && exit 1; \
  	fi;
	@find $(TF_RUNNER_DIR) -name '*.egg-info' -exec rm -rf {} +
	@aws s3 cp $(TF_RUNNER_DIST_FILE_PATH) s3://$(BOOTSTRAP_BUCKET)/dist/$(TF_RUNNER_DIST_FILE)

ifeq ($(VALID_ACCOUNT_ID),)
	$(error [ERROR] Unable to determine the ID of your AWS account, please ensure \
	your AWS credentials are valid and your profile is configured properly)
endif

ifeq ($(strip $(AWS_REGION)),)
	$(error [ERROR] Unable to determine the correct AWS region, please ensure your \
	 desired region is properly defined in your environment)
endif

install-terraform-runner: upgrade-pip
	@$(BIN)/pip3 install --require-virtualenv --editable $(TF_RUNNER_DIR)
	@find $(TF_RUNNER_DIR) -name '*.egg-info' -exec rm -rf {} +

test-tf-runner: install-terraform-runner
	@$(BIN)/python3 -m unittest discover --verbose \
	--start-directory $(TF_RUNNER_DIR)/terraform_runner



# ========================================================================
# 							Lambda Function Targets
# ========================================================================
# The AWS SAM build operation is configured to use build containers and
# before executing, this target will check that Docker is installed and
# verify the Docker daemon is running.
build-lambda-functions: upgrade-pip check-docker
	@$(BIN)/sam build --config-file $(SAM_CONFIG_FILE) \
       --config-env $(SAM_CONFIG_ENV) \
	   --template-file $(SAM_TEMPLATE_FILE)
	@rm -f "$(SAM_ROOT_DIR)/packaged.yaml"
	@echo
	@$(BIN)/sam package --no-progressbar \
       --s3-bucket $(BOOTSTRAP_BUCKET) --s3-prefix "dist" \
       --output-template-file "$(SAM_ROOT_DIR)/packaged.yaml"
	@if [ ! -e "$(SAM_ROOT_DIR)/packaged.yaml" ]; then \
  	   echo "[ERROR] No AWS SAM packaged template file found at path ` \
  	     `$(SAM_ROOT_DIR)/packaged.yaml"; \
  	fi;

# Directly build binaries for the Terraform Parameter Parser function on your local
# system. This is a convenience target for local development and requires that Go be
# properly installed on your local system.
build-local-parameter-parser: check-go
	@$(info $(shell echo "Local System OS: $$(go env GOOS), \
		Local System Architecture: $$(go env GOARCH)"))
	@if [ -e $(PARAM_PARSER_DIR)/go.mod ]; then \
		rm -f $(PARAM_PARSER_DIR)/go.mod; \
		cd $(PARAM_PARSER_DIR) || exit 1; \
  		go mod init terraform_open_source_parameter_parser; \
  		go env -w GOPROXY=direct; \
  		go mod tidy; \
  	fi
	@rm -rf $(PARAM_PARSER_DIR)/bin && mkdir -p $(PARAM_PARSER_DIR)/bin
	@cd $(PARAM_PARSER_DIR) && {\
		CGO_ENABLED=0 go build -o bin/$$(go env GOOS)-$$(go env GOARCH)/terraform_open_source_parameter_parser; \
		CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o bin/linux-amd64/terraform_open_source_parameter_parser; \
		echo "$(PARAM_PARSER_DIR)/bin/$$(go env GOOS)-$$(go env GOARCH)/terraform_open_source_parameter_parser"; \
		echo "$(PARAM_PARSER_DIR)/bin/linux-amd64/terraform_open_source_parameter_parser"; \
	}

# Directly execute the tests for the Terraform Parameter Parser function on your local
# system. This is a convenience target for local development and requires that Go be
# properly installed on your local system.
test-param-parser: check-go
	@cd $(PARAM_PARSER_DIR) && go test -v

test-provisioning-handler: upgrade-pip
	@$(BIN)/python3 -m unittest discover --verbose --start-directory $(OPS_HANDLER_DIR)

test-state-machine: upgrade-pip
	@$(BIN)/python3 -m unittest discover --verbose --start-directory $(STATE_MACHINE_DIR)

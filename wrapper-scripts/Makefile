# ===============================================================================
# 							Global Environment Configuration
# ===============================================================================
VENV_DIR := .venv
BIN := $(VENV_DIR)/bin
SHELL := /bin/bash


# ===============================================================================
# 							Dynamic Environment Configuration
# ===============================================================================
SYSTEM_PYTHON := $(or $(shell which python3), "/usr/bin/python3")
AWS_ACCOUNT_ID := $(shell aws sts get-caller-identity --output text --query Account 2>&1)
AWS_REGION := $(shell echo $${AWS_REGION:-$$AWS_DEFAULT_REGION})
AWS_REGION := $(or $(AWS_REGION), $(shell echo $${AWS_PROFILE_REGION}))
BOOTSTRAP_BUCKET := terraform-engine-bootstrap-$(AWS_ACCOUNT_ID)-$(AWS_REGION)


# ===============================================================================
# 						  	Terraform Runner Configuration
# ===============================================================================
TF_RUNNER_DIR := .
TF_RUNNER_VER := $(shell head -n 1 $(TF_RUNNER_DIR)/terraform_runner/__init__.py | awk '{print $$3}' | xargs)
TF_RUNNER_DIST_FILE := terraform_runner-$(TF_RUNNER_VER)-py3-none-any.whl
TF_RUNNER_DIST_FILE_PATH := $(TF_RUNNER_DIR)/dist/$(TF_RUNNER_DIST_FILE)


# ===============================================================================
#                           Global Shortcut Targets
# ===============================================================================
all: venv upgrade-pip test
build: build-terraform-runner
test: test-tf-runner
.PHONY: all build build-terraform-runner check-prerequisites clean install-terraform-runner test test-tf-runner upgrade-pip venv



# ===============================================================================
#                           Global Convenience Targets
# ===============================================================================
help:
	@echo "venv    - create a virtualenv with all baseline dependencies installed"
	@echo "build   - package new code and build binary distributions of the local package"
	@echo "clean   - remove build, test, coverage and Python artifacts locally"
	@echo "test    - run all unit tests for the local package"

clean:
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
PREREQS := aws python3
check-prerequisites:
	@for cmd in $(PREREQS); do \
		command -v $$cmd >/dev/null 2>&1 || \
		{ echo >&2 "$$cmd is required but it's not installed, aborting."; exit 1; }; \
	done



# ===============================================================================
#                           Python Virtual Environment
# ===============================================================================
venv: check-prerequisites $(VENV_DIR)

$(VENV_DIR): $(TF_RUNNER_DIR)/requirements.txt
	@$(SYSTEM_PYTHON) -m venv $(VENV_DIR)
	@$(BIN)/pip3 install --require-virtualenv --quiet --upgrade pip build setuptools
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

deploy-terraform-runner-build: upgrade-pip test-tf-runner $(TF_RUNNER_DIST_FILE_PATH)
	@aws s3 cp $(TF_RUNNER_DIST_FILE_PATH) s3://$(BOOTSTRAP_BUCKET)/dist/$(TF_RUNNER_DIST_FILE)

ifeq ($(strip $(AWS_ACCOUNT_ID) | egrep "^[0-9]{12}$$"),)
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

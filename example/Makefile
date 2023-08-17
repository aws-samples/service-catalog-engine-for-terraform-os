# ===============================================================================
# 							Global Environment Configuration
# ===============================================================================
PROJECT_ROOT_DIR := $(shell git rev-parse --show-toplevel)
EXAMPLE_DIR := "$(PROJECT_ROOT_DIR)/example"
PARAMS_DIR := "$(EXAMPLE_DIR)/.parameters"
SYSTEM_PYTHON := $(or $(shell which python3), "/usr/bin/python3")



# ===============================================================================
# 							Dynamic Environment Configuration
# ===============================================================================
AWS_ACCOUNT_ID ?= $(shell aws sts get-caller-identity --output text --query Account 2>&1)
VALID_ACCOUNT_ID := $(shell echo $(AWS_ACCOUNT_ID) | egrep "^[0-9]{12}$$")
AWS_REGION := $(shell echo $${AWS_REGION:-$$AWS_DEFAULT_REGION})
AWS_REGION := $(or $(AWS_REGION), $(shell echo $${AWS_PROFILE_REGION}))
BOOTSTRAP_BUCKET ?= terraform-engine-bootstrap-$(AWS_ACCOUNT_ID)-$(AWS_REGION)



# ========================================================================
# 						Terraform Example Configuration
# =======================================================================
ARTIFACT_URL := "https://$(BOOTSTRAP_BUCKET).s3.$(AWS_REGION).amazonaws.com/dist/terraform-example-bucket.tar.gz"
EXAMPLE_PREFIX := 'Terraform Example - '
LAUNCH_ROLE_NAME := "SCLaunchRoleTerraformBucketExample-$(AWS_REGION)"
LAUNCH_ROLE_STACK_NAME := "terraform-example-launch-role"
SHARED_ROLE_NAME ?= "AWSReservedSSO_AWSServiceCatalogEndUserAccess*"
SHARED_ROLE_ARN := "arn:aws:iam:::role/**/$(SHARED_ROLE_NAME)"
SHARED_OU_ID ?= ""
VALID_SHARED_OU_ID := $(shell echo $(SHARED_OU_ID) | egrep "^ou-[0-9a-z]{4,32}-[a-z0-9]{8,32}$$")
VALID_SHARED_ROLE_NAME := $(shell echo $(SHARED_ROLE_NAME) | egrep "^[\w+=,.@-\*]{1,64}")



# ===============================================================================
#                           Global Shortcut Targets
# ===============================================================================
all: check-prerequisites
create-terraform-example: check-prerequisites build-provisioning-artifact create-launch-role create-product create-portfolio \
   create-product-association create-constraint
delete-terraform-example: check-prerequisites unshare-portfolio revoke-portfolio-access delete-portfolio delete-product \
   delete-launch-role

.PHONY: all build-provisioning-artifact check-prerequisites create-launch-role create-product create-portfolio \
   create-product-association create-constraint create-terraform-example delete-launch-role delete-portfolio \
   delete-product delete-terraform-example revoke-portfolio-access unshare-portfolio



# ===============================================================================
#                           Global Convenience Targets
# ===============================================================================
help:
	@echo "check-prerequisites          - create a virtualenv with all baseline dependencies installed"
	@echo "create-terraform-example     - package new code and build binary distributions of all local packages"
	@echo "delete-terraform-example     - package new code and build binary distributions of all local packages"
	@echo "create-example-launch-role   - run all unit tests for all local packages"



# ========================================================================
#                           Prerequisite Checks
# ========================================================================
check-prerequisites: prerequisites
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



# ========================================================================
# 						Terraform Example Module Targets
# ========================================================================
build-provisioning-artifact: prerequisites
	@echo "Building provisioning artifact and copying to the bootstrap S3 bucket."
	@rm -f $(EXAMPLE_DIR)/terraform-example-bucket.tar.gz
	@cd $(EXAMPLE_DIR)/terraform-example-bucket/ && \
	   tar -zcf ../terraform-example-bucket.tar.gz *
	@if [ ! -e $(EXAMPLE_DIR)/terraform-example-bucket.tar.gz ]; then \
  	   echo "  - [ERROR] Build failed: no provisioning artifact found at path ` \
  	   `$(EXAMPLE_DIR)/terraform-example-bucket.tar.gz." && exit 1; \
  	fi
	@aws s3 cp $(EXAMPLE_DIR)/terraform-example-bucket.tar.gz \
	   s3://$(BOOTSTRAP_BUCKET)/dist/terraform-example-bucket.tar.gz > /dev/null
	@$(SYSTEM_PYTHON) -c \
       "import json; \
		data = json.load(open('$(PARAMS_DIR)/terraform-example-product-params.json', 'r')); \
		data['ProvisioningArtifactParameters']['Info']['LoadTemplateFromURL'] = '$(ARTIFACT_URL)'; \
		json.dump(data, open('$(PARAMS_DIR)/terraform-example-product-params.json', 'w'), indent=4)"
	@echo "  - Provisioning Artifact: s3://$(BOOTSTRAP_BUCKET)/dist/terraform-example-bucket.tar.gz"

create-constraint: prerequisites
	@echo "Creating launch constraint for the Service Catalog product and portfolio in ` \
	   `AWS account $(AWS_ACCOUNT_ID)."
	@sleep 5
	@product_id=$$(aws servicecatalog search-products-as-admin \
	  --query "ProductViewDetails[?starts_with(ProductViewSummary.Name, \
	  $(EXAMPLE_PREFIX))].ProductViewSummary.ProductId | [0]" \
	  --output text | grep -v "None"); \
  	portfolio_id=$$(aws servicecatalog list-portfolios \
	  --query "PortfolioDetails[?starts_with(DisplayName, $(EXAMPLE_PREFIX))].Id | [0]" \
	  --output text | grep -v "None"); \
	if [[ -n "$${product_id}" && -n "$${portfolio_id}" ]]; then \
	  constraint_id=$$(aws servicecatalog list-constraints-for-portfolio \
	    --portfolio-id "$${portfolio_id}" 2>&1 | \
		grep '"ConstraintId":' | awk -F'"' '{print $$4}'); \
	  if [[ -z "$${constraint_id}" ]]; then \
	    constraint_id=$$(aws servicecatalog create-constraint \
		  --product-id "$${product_id}" --type LAUNCH \
		  --portfolio-id "$${portfolio_id}" \
		  --parameters '{"LocalRoleName": $(LAUNCH_ROLE_NAME)}' | \
		  grep '"ConstraintId":' | awk -F'"' '{print $$4}'); \
	  fi; \
	  echo "  - Service Catalog Constraint: $${constraint_id}"; \
	else \
	  echo "  - [ERROR] Either the Service Catalog product or portfolio do not exist in AWS ` \
  	  	`account $(AWS_ACCOUNT_ID) and region $(AWS_REGION)"; exit 1; \
	fi;

create-launch-role: prerequisites
	@echo "Creating the IAM role in AWS account $(AWS_ACCOUNT_ID) for the Service Catalog ` \
	   `launch constraint."
	@launch_role_arn=$$(aws cloudformation describe-stacks \
       --stack-name $(LAUNCH_ROLE_STACK_NAME) 2>&1 | \
       grep '"OutputValue": "arn:' | awk -F'"' '{print $$4}'); \
	if [[ -z "$${launch_role_arn}" ]]; then \
	  aws cloudformation create-stack \
	    --stack-name $(LAUNCH_ROLE_STACK_NAME) \
	    --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
	    --template-body file://"$(EXAMPLE_DIR)/terraform-example-launch-role.yaml" \
	    --parameters ParameterKey=TerraformEngineAccount,ParameterValue=$(AWS_ACCOUNT_ID) \
	    --region $(AWS_REGION) > /dev/null; \
	  sleep 30; \
	  launch_role_arn=$$(aws cloudformation describe-stacks \
	    --stack-name $(LAUNCH_ROLE_STACK_NAME) 2>&1 | \
		grep '"OutputValue": "arn:' | awk -F'"' '{print $$4}'); \
	  if [[ -z "$${launch_role_arn}" ]]; then \
	    echo "  - [ERROR] An error occurred while creating the IAM role in AWS account $(AWS_ACCOUNT_ID), ` \
	      `CloudFormation Stack $(LAUNCH_ROLE_STACK_NAME) not found in region $(AWS_REGION)."; exit 1; \
	  fi; \
	fi; \
	echo "  - Launch Role: $${launch_role_arn}"

create-product-association: prerequisites
	@echo "Associating the Service Catalog product with the portfolio in AWS account ` \
	   `$(AWS_ACCOUNT_ID)."
	@sleep 1.5
	@product_id=$$(aws servicecatalog search-products-as-admin \
	  --query "ProductViewDetails[?starts_with(ProductViewSummary.Name, \
	  $(EXAMPLE_PREFIX))].ProductViewSummary.ProductId | [0]" \
	  --output text | grep -v "None"); \
	portfolio_id=$$(aws servicecatalog list-portfolios \
	  --query "PortfolioDetails[?starts_with(DisplayName, $(EXAMPLE_PREFIX))].Id | [0]" \
	  --output text | grep -v "None"); \
	if [[ -n "$${product_id}" && -n "$${portfolio_id}" ]]; then \
	  aws servicecatalog associate-product-with-portfolio \
	    --portfolio-id "$${portfolio_id}" --product-id "$${product_id}"; \
	  echo "  - Product Association: $${product_id} with $${portfolio_id}"; \
	else \
	  echo "  - [ERROR] Either the Service Catalog product or portfolio do not exist in AWS ` \
  	  	`account $(AWS_ACCOUNT_ID) and region $(AWS_REGION)"; exit 1; \
	fi

create-portfolio: prerequisites
	@echo "Creating the Service Catalog portfolio in AWS account $(AWS_ACCOUNT_ID)."
	@portfolio_id=$$(aws servicecatalog list-portfolios \
	  --query "PortfolioDetails[?starts_with(DisplayName, $(EXAMPLE_PREFIX))].Id | [0]" \
	  --output text | grep -v "None"); \
	if [[ -z "$${portfolio_id}" ]]; then \
	  portfolio_id=$$(aws servicecatalog create-portfolio \
	    --cli-input-json file://$(PARAMS_DIR)/terraform-example-portfolio-params.json | \
	    grep '"Id":' | awk -F'"' '{print $$4}'); \
	fi; \
    echo "  - Service Catalog Portfolio: $${portfolio_id}"

create-product: prerequisites build-provisioning-artifact
	@echo "Creating the Service Catalog product in AWS account $(AWS_ACCOUNT_ID)."
	@product_id=$$(aws servicecatalog search-products-as-admin \
	  --query "ProductViewDetails[?starts_with(ProductViewSummary.Name, \
	  $(EXAMPLE_PREFIX))].ProductViewSummary.ProductId | [0]" \
	  --output text | grep -v "None"); \
	if [[ -z "$${product_id}" ]]; then \
	  product_id=$$(aws servicecatalog create-product \
	    --cli-input-json file://$(PARAMS_DIR)/terraform-example-product-params.json | \
		grep '"ProductId":' | awk -F'"' '{print $$4}'); \
	fi; \
	echo "  - Service Catalog Product: $${product_id}"

delete-launch-role: prerequisites
	@echo "Deleting the IAM role in AWS account $(AWS_ACCOUNT_ID) used for the Service Catalog ` \
	   `launch constraint."
	@stack_result=$$(aws cloudformation describe-stacks \
	   --stack-name $(LAUNCH_ROLE_STACK_NAME) 2>&1); \
	stack_id=$$(echo "$${stack_result}" | grep '"StackId": "arn:' | \
	  awk -F'"' '{print $$4}'); \
	if [[ -n "$${stack_id}" ]]; then \
	  aws cloudformation delete-stack --stack-name $(LAUNCH_ROLE_STACK_NAME); \
	  sleep 30; \
	  stack_deleted=$$(aws cloudformation describe-stacks \
	    --stack-name $(LAUNCH_ROLE_STACK_NAME) 2>&1 | egrep 'does not exist$$'); \
	  if [[ -n "$${stack_deleted}" ]]; then \
	    launch_role_arn=$$(echo "$${stack_result}" | grep '"OutputValue": "arn:' | \
	      awk -F'"' '{print $$4}'); \
	    echo "  - Deleted Launch Role: $${launch_role_arn}"; \
	  else \
	    echo "  - [ERROR] An error occurred while attempting to delete the IAM role in AWS ` \
	      `account $(AWS_ACCOUNT_ID), please remove CloudFormation Stack $${stack_id}."; \
	  fi; \
  	else \
  	  echo "  - [ERROR] The IAM role does not exist in AWS account $(AWS_ACCOUNT_ID)."; \
  	fi

delete-product-associations: prerequisites
	@echo "Removing the Service Catalog product association with the portfolio in AWS ` \
	   `account $(AWS_ACCOUNT_ID)."
	@product_id=$$(aws servicecatalog search-products-as-admin \
	  --query "ProductViewDetails[?starts_with(ProductViewSummary.Name, \
	  $(EXAMPLE_PREFIX))].ProductViewSummary.ProductId | [0]" \
	  --output text | grep -v "None"); \
	if [[ -n "$${product_id}" ]]; then \
	  portfolio_ids=($$(aws servicecatalog list-portfolios-for-product \
	    --query 'PortfolioDetails[].Id' --output text \
	    --product-id "$${product_id}" | xargs)); \
	  for portfolio_id in $${portfolio_ids[@]}; do \
	    sleep 1.5; \
	    aws servicecatalog disassociate-product-from-portfolio \
		  --product-id "$${product_id}" --portfolio-id "$${portfolio_id}"; \
		echo "  - Deleted Product Association: $${product_id} from $${portfolio_id}"; \
	  done; \
	else \
	  echo "  - [ERROR] The Service Catalog product does not exist in AWS account ` \
	  	`$(AWS_ACCOUNT_ID) and region $(AWS_REGION), nothing to remove."; \
	fi

delete-portfolio: delete-product-associations
	@echo "Deleting the Service Catalog portfolio from AWS account $(AWS_ACCOUNT_ID)."
	@portfolio_id=$$(aws servicecatalog list-portfolios \
	  --query "PortfolioDetails[?starts_with(DisplayName, $(EXAMPLE_PREFIX))].Id | [0]" \
	  --output text | grep -v "None"); \
	if [[ -n "$${portfolio_id}" ]]; then \
	  aws servicecatalog delete-portfolio --id "$${portfolio_id}"; \
	  echo "  - Deleted Service Catalog Portfolio: $${portfolio_id}"; \
	else \
	  echo "  - [ERROR] The Service Catalog portfolio does not exist in AWS account ` \
	    `$(AWS_ACCOUNT_ID) and region $(AWS_REGION)."; \
	fi

delete-product: prerequisites
	@echo "Deleting the Service Catalog product from AWS account $(AWS_ACCOUNT_ID)."
	@product_id=$$(aws servicecatalog search-products-as-admin \
	  --query "ProductViewDetails[?starts_with(ProductViewSummary.Name, \
	  $(EXAMPLE_PREFIX))].ProductViewSummary.ProductId | [0]" \
	  --output text | grep -v "None"); \
	if [[ -n "$${product_id}" ]]; then \
		aws servicecatalog delete-product --id "$${product_id}"; \
		echo "  - Deleted Service Catalog Product: $${product_id}"; \
	else \
	  echo "  - [ERROR] The Service Catalog product does not exist in AWS account ` \
	  	`$(AWS_ACCOUNT_ID) and region $(AWS_REGION)."; \
	fi

grant-portfolio-access: prerequisites
	@echo "Granting access to the Service Catalog portfolio in $(AWS_ACCOUNT_ID) to any ` \
	   `IAM roles matching the following pattern: $(SHARED_ROLE_ARN)"
	@portfolio_id=$$(aws servicecatalog list-portfolios \
	   --query "PortfolioDetails[?starts_with(DisplayName, $(EXAMPLE_PREFIX))].Id | [0]" \
	   --output text | grep -v "None"); \
	if [[ -n "$${portfolio_id}" ]]; then \
	  aws servicecatalog associate-principal-with-portfolio \
	    --portfolio-id "$${portfolio_id}" --principal-type IAM_PATTERN \
	    --principal-arn "$(SHARED_ROLE_ARN)"; \
	  echo "  - Granted Portfolio Access: $(SHARED_ROLE_ARN)"; \
	else \
	  echo "  - [ERROR] The Service Catalog portfolio does not exist in AWS account ` \
	    `$(AWS_ACCOUNT_ID) and region $(AWS_REGION)."; exit 1; \
	fi
ifeq ($(VALID_SHARED_ROLE_NAME), )
	$(error [ERROR] No IAM role name or name pattern set or the specified value is invalid, please \
	ensure you have set a valid IAM role name or name pattern in the SHARED_ROLE_NAME variable)
endif

revoke-portfolio-access: prerequisites
	@echo "Revoking access to the Service Catalog portfolio in $(AWS_ACCOUNT_ID) for ` \
	   `all defined IAM role patterns."
	@portfolio_id=$$(aws servicecatalog list-portfolios \
	   --query "PortfolioDetails[?starts_with(DisplayName, $(EXAMPLE_PREFIX))].Id | [0]" \
	   --output text | grep -v "None"); \
	if [[ -n "$${portfolio_id}" ]]; then \
	  principal_arns=($$(aws servicecatalog list-principals-for-portfolio \
	    --portfolio-id "$${portfolio_id}" \
	    --query 'Principals[].PrincipalARN' --output text | xargs)); \
  	  for principal_arn in $${principal_arns[@]}; do \
  	  	sleep 1.5; \
  	    aws servicecatalog disassociate-principal-from-portfolio \
	      --portfolio-id "$${portfolio_id}" --principal-type IAM_PATTERN \
	      --principal-arn "$${principal_arn}"; \
	  	echo "  - Revoked Portfolio Access: $${principal_arn}"; \
	  done; \
	else \
	  echo "  - [ERROR] The Service Catalog portfolio does not exist in AWS account ` \
	    `$(AWS_ACCOUNT_ID) and region $(AWS_REGION), nothing to revoke."; \
	fi

share-portfolio: prerequisites
	@echo "Sharing the Service Catalog portfolio in $(AWS_ACCOUNT_ID) with the AWS ` \
	   `Organizations OU: $(SHARED_OU_ID)"
	@portfolio_id=$$(aws servicecatalog list-portfolios \
	  --query "PortfolioDetails[?starts_with(DisplayName, $(EXAMPLE_PREFIX))].Id | [0]" \
	  --output text | grep -v "None"); \
	if [[ -n "$${portfolio_id}" ]]; then \
	  aws servicecatalog create-portfolio-share \
	    --portfolio-id "$${portfolio_id}" --share-principals --share-tag-options \
	    --organization-node Type=ORGANIZATIONAL_UNIT,Value=$(SHARED_OU_ID) >/dev/null; \
	  echo "  - Portfolio Share: $(SHARED_OU_ID)"; \
	else \
	  echo "  - [ERROR] The Service Catalog portfolio does not exist in AWS account ` \
	  	`$(AWS_ACCOUNT_ID) and region $(AWS_REGION)."; exit 1; \
	fi
ifeq ($(VALID_SHARED_OU_ID),)
	$(error [ERROR] No AWS Organizations OU ID set or the specified value is invalid, please \
	ensure you have set a valid OU ID in the SHARED_OU_ID variable)
endif

unshare-portfolio: prerequisites
	@echo "Removing all Service Catalog portfolio shares in AWS account ` \
	   `$(AWS_ACCOUNT_ID)."
	@portfolio_id=$$(aws servicecatalog list-portfolios \
	  --query "PortfolioDetails[?starts_with(DisplayName, $(EXAMPLE_PREFIX))].Id | [0]" \
	  --output text | grep -v "None"); \
	if [[ -n "$${portfolio_id}" ]]; then \
	  ou_ids=($$(aws servicecatalog describe-portfolio-shares \
	    --portfolio-id "$${portfolio_id}" --type ORGANIZATIONAL_UNIT \
	    --query 'PortfolioShareDetails[].PrincipalId' --output text | xargs)); \
  	  for ou_id in $${ou_ids[@]}; do \
  	    sleep 1.5; \
  	    aws servicecatalog delete-portfolio-share \
	      --organization-node Type=ORGANIZATIONAL_UNIT,Value="$${ou_id}" \
	  	  --portfolio-id "$${portfolio_id}" >/dev/null; \
	    echo "  - Removed Portfolio Share: $${ou_id}"; \
  	  done; \
	else \
	  echo "  - [ERROR] The Service Catalog portfolio does not exist in AWS account ` \
	  	`$(AWS_ACCOUNT_ID) and region $(AWS_REGION), nothing to remove."; \
	fi

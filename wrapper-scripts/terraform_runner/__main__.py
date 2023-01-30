import argparse
import json
import os
import sys
import traceback

from terraform_runner.artifact_manager import download_artifact
from terraform_runner.CommandManager import CommandManager
from terraform_runner.CustomLogger import CustomLogger
from terraform_runner.override_manager import write_backend_override, write_variable_override, write_provider_override
from terraform_runner.WorkspaceManager import WorkspaceManager


# Constants
APPLY_ACTION = 'apply'
DESTROY_ACTION = 'destroy'
AWS_DEFAULT_REGION = 'AWS_DEFAULT_REGION'


def __parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--action', help = 'The action to perform', choices = [APPLY_ACTION, DESTROY_ACTION])
    parser.add_argument('--provisioned-product-descriptor', 
        help = 'A descriptor that uniquely identifies a provisioned product')
    parser.add_argument('--launch-role', help = 'The launch role Arn')
    parser.add_argument('--region',
        help = 'The region where resources will be provisioned and where the Terraform state will be stored')
    parser.add_argument('--terraform-state-bucket', 
        help = 'The bucket where the Terraform state will be stored')
    parser.add_argument('--artifact-path', help = 'The artifact S3 path in URI format')
    parser.add_argument('--artifact-parameters', type = json.loads,
        help = 'Artifact parameters in json format')
    parser.add_argument('--tags', type = json.loads,
        help = 'Tags to apply to the provisioned resources, in json format')
    return parser.parse_args()

def __set_environment_variables(args):
    os.environ[AWS_DEFAULT_REGION] = args.region

def __setup_workspace(workspace_manager):
    workspace_manager.setup_workspace_directory()
    workspace_dir = workspace_manager.get_workspace_directory()
    os.chdir(workspace_dir)
    return workspace_dir

def __write_common_overrides(workspace_dir, args):
    write_backend_override(workspace_dir, args.provisioned_product_descriptor, 
        args.terraform_state_bucket, args.region)
    write_provider_override(workspace_dir, args.provisioned_product_descriptor, args.launch_role,
        args.region, args.tags)

def __perform_apply(command_manager, workspace_dir, args):
    download_artifact(args.launch_role, args.artifact_path, workspace_dir)
    write_variable_override(workspace_dir, args.artifact_parameters)
    command_manager.run_command(['terraform', 'init', '-no-color'])
    command_manager.run_command(['terraform', 'validate', '-no-color'])
    command_manager.run_command(['terraform', 'apply', '-auto-approve', '-input=false', '-compact-warnings', '-no-color'])

def __perform_destroy(command_manager):
    command_manager.run_command(['terraform', 'init', '-no-color'])
    command_manager.run_command(['terraform', 'validate', '-no-color'])
    command_manager.run_command(['terraform', 'destroy', '-auto-approve', '-no-color'])

def main():
    args = __parse_arguments()
    log = CustomLogger(args.provisioned_product_descriptor)
    log.info(f'Command args: {args}')

    command_manager = CommandManager(log)
    workspace_manager = WorkspaceManager(log, args.provisioned_product_descriptor)

    exit_code = 0
    try:
        __set_environment_variables(args)

        workspace_dir = __setup_workspace(workspace_manager)
        __write_common_overrides(workspace_dir, args)

        # Perform the action
        if args.action == APPLY_ACTION:
            __perform_apply(command_manager, workspace_dir, args)
        elif args.action == DESTROY_ACTION:
            __perform_destroy(command_manager)

    except Exception as exception:
        message = str(exception)
        # Log every exception with traceback in a single place.
        log.error(f'{message} {traceback.format_exc()}' )
        # Then exit with error status, only writing the exception message to stderr
        exit_code = message

    finally:
        log.info(f'Removing workspace directory {workspace_dir}')
        workspace_manager.remove_workspace_directory()

    sys.exit(exit_code)


if __name__ == '__main__':
    main()

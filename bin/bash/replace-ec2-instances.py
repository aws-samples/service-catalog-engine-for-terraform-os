import math
import os
import time

import boto3

AWS_REGION_KEY = 'AWS_REGION'
AWAIT_SECONDS = 10
INSTANCE_NAME = 'TerraformEngineExecutionInstance'
INSTANCE_FILTERS = [
        {'Name': 'tag:Name', 'Values': [INSTANCE_NAME]}
    ]

if AWS_REGION_KEY in os.environ and os.environ[AWS_REGION_KEY]:
    aws_region = os.environ[AWS_REGION_KEY]
else:
    raise RuntimeError(f'Environment variable {AWS_REGION_KEY} has not been set.')

lambda_client = boto3.client('lambda', region_name = aws_region)
step_functions_client = boto3.client('stepfunctions', region_name = aws_region)
ec2_client = boto3.client('ec2', region_name = aws_region)
autoscaling_client = boto3.client('autoscaling', region_name = aws_region)

def get_event_source_mapping_uuid_tuples(function_names):
    function_name_uuid_tuples = []
    for function_name in function_names:
        print(f'Getting event source mappings for function {function_name}')
        # Not paginating here because we know we have no more than two mappings per function
        response = lambda_client.list_event_source_mappings(FunctionName = function_name)
        for event_source_mapping in response['EventSourceMappings']:
            function_name_uuid_tuples.append((function_name, event_source_mapping['UUID']))
    return function_name_uuid_tuples

def await_event_source_mapping_state(uuid, required_state):
    print(f'Waiting for event source mapping state: {required_state}. {uuid}')
    current_state = ''
    while current_state != required_state:
        time.sleep(AWAIT_SECONDS)
        response = lambda_client.get_event_source_mapping(UUID = uuid)
        current_state = response['State']
        print(f'Event source mapping state is {current_state}. {uuid}')

def update_event_source_mappings(function_name_uuid_tuples, enabled):
    for function_name_uuid_tuple in function_name_uuid_tuples:
        print(f'Updating event source mapping with enabled={enabled}: {function_name_uuid_tuple}')
        lambda_client.update_event_source_mapping(FunctionName = function_name_uuid_tuple[0], UUID = function_name_uuid_tuple[1], Enabled = enabled)
        # The update is an asynchronous operation, so await its completion.
        required_state = 'Enabled' if enabled else 'Disabled'
        await_event_source_mapping_state(function_name_uuid_tuple[1], required_state)

def get_state_machine_arn(state_machine_name):
    print(f'Getting state machine arn for {state_machine_name}')
    page_iterator = step_functions_client.get_paginator('list_state_machines').paginate()
    for page in page_iterator:
        for state_machine in page['stateMachines']:
            if state_machine['name'] == state_machine_name:
                return state_machine['stateMachineArn']
    raise RuntimeError(f'No state machine arn could be found for {state_machine_name}')

def drain_state_machine_executions(state_machine_name):
    state_machine_arn = get_state_machine_arn(state_machine_name)
    print(f'Draining state machine executions for {state_machine_arn}')
    while True:
        # Not paginating here. We only care if there are more than zero executions.
        response = step_functions_client.list_executions(stateMachineArn = state_machine_arn, statusFilter = 'RUNNING')
        execution_count = len(response['executions'])
        print(f'Found {execution_count} running state machine executions for {state_machine_arn}')
        if execution_count == 0:
            break
        time.sleep(AWAIT_SECONDS)

def get_instance_ids(filters):
    print(f'Getting EC2 instance IDs for filters: {filters}')
    paginator = ec2_client.get_paginator('describe_instances')
    page_iterator = paginator.paginate(Filters = filters)

    instances = []
    for page in page_iterator:
        for reservation in page['Reservations']:
            instances += reservation['Instances']

    return [instance['InstanceId'] for instance in instances]

def terminate_terraform_ec2_instances():
    instance_ids = get_instance_ids(INSTANCE_FILTERS)
    print(f'Terminating Terraform EC2 instances: {instance_ids}')
    responce = ec2_client.terminate_instances(InstanceIds = instance_ids)
    instance_id_count = len(instance_ids)
    terminating_instance_count = len(responce['TerminatingInstances'])
    if instance_id_count != terminating_instance_count:
        raise RuntimeError(f'Expected {instance_id_count} instances to be terminated, but only {terminating_instance_count} are actually being terminated.')

def await_running_terraform_ec2_instances():
    autoscaling_response = autoscaling_client.describe_auto_scaling_groups(AutoScalingGroupNames = ['TerraformAutoscalingGroup'])
    autoscaling_desired_capacity = autoscaling_response['AutoScalingGroups'][0]['DesiredCapacity']
    print(f'Waiting for running Terraform EC2 instances. Autoscaling desired capacity is {autoscaling_desired_capacity}.')

    filters = INSTANCE_FILTERS
    filters.append({'Name': 'instance-state-name', 'Values': ['running']})
    while True:
        time.sleep(AWAIT_SECONDS)
        instance_ids = get_instance_ids(filters)
        instance_id_count = len(instance_ids)
        print(f'Found {instance_id_count} instances. Waiting for {autoscaling_desired_capacity} running instances.')
        if instance_id_count >= autoscaling_desired_capacity:
            break

# Main
start_time = time.time()
print('Pausing SQS message processing in order to safely replace the Terraform EC2 instances.')
print('This may take a few minutes.')

event_source_mapping_uuid_tuples = get_event_source_mapping_uuid_tuples(['TerraformEngineProvisioningHandlerLambda', 'TerraformEngineTerminateHandlerLambda'])
update_event_source_mappings(event_source_mapping_uuid_tuples, False)
print('Event source mappings have been disabled. SQS messages will remain in their queues until they are enabled.')

drain_state_machine_executions('ManageProvisionedProductStateMachine')
drain_state_machine_executions('TerminateProvisionedProductStateMachine')
print('All state machine executions have finished. Ready to replace EC2 instances.')

terminate_terraform_ec2_instances()
await_running_terraform_ec2_instances()

update_event_source_mappings(event_source_mapping_uuid_tuples, True)
print('Event source mappings have been enabled. SQS message processing will now resume.')
print(f'The instance replacement process took{math.floor(time.time() - start_time)} seconds.')

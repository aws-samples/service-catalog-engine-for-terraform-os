import logging
import random

import boto3

from core.configuration import Configuration
from core.exception import log_exception

log = logging.getLogger()
log.setLevel(logging.INFO)

app_config = None
ec2_client = None

# EC2 client keys
FILTERS: list = [
    {
        'Name': 'tag:Name',
        'Values': ['TerraformEngineExecutionInstance']
    },
    {
        'Name': 'instance-state-name',
        'Values': ['running']
    }
]
RESERVATIONS = 'Reservations'
INSTANCES = 'Instances'
EC2_RESPONSE_INSTANCE_ID = 'InstanceId'
ERROR_RESPONSE_METADATA = 'ResponseMetadata'
REQUEST_ID = 'RequestId'
ERROR = 'Error'
ERROR_RESPONSE_MESSAGE = 'Message'

# Lambda response keys
RETURNED_INSTANCE_ID = 'instanceId'


def __select_random_instance_id():
    """Randomly selects a running EC2 instance that matches the designated tag"""
    instances = []

    describe_instances_paginator = ec2_client.get_paginator('describe_instances')
    describe_instances_iterator = describe_instances_paginator.paginate(
        Filters=FILTERS
    )

    for page in describe_instances_iterator:
        for reservation in page[RESERVATIONS]:
            instances += reservation[INSTANCES]

    if not instances:
        raise RuntimeError('No usable EC2 instances found')

    index = random.randint(0, len(instances) - 1)
    return instances[index][EC2_RESPONSE_INSTANCE_ID]


def select(event, context) -> object:
    """Lambda function to select an EC2 instance from the auto-scaling group

    Parameters
    ----------
    event: dict, required
        The input event to the Lambda function

    context: object, required
        Lambda Context runtime methods and attributes

    Returns
    ------
        dict: A randomly selected instance ID
    """
    global app_config
    global ec2_client

    try:
        if not app_config:
            app_config = Configuration()
        if not ec2_client:
            ec2_client = boto3.client('ec2', config=app_config.get_boto_config())

        response = {
            RETURNED_INSTANCE_ID: __select_random_instance_id()
        }
        log.info(f'Returning {response}')
        return response

    except Exception as e:
        log_exception(e)
        raise e

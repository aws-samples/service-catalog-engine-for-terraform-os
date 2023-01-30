import os

from botocore.config import Config

# Constants
USER_AGENT: str = 'TerraformReferenceEngine-1.0'

class Configuration:

    def __init__(self):
        self.__aws_region: str = os.environ['AWS_REGION']
        self.__boto_config = Config(
            region_name=self.__aws_region,
            user_agent=USER_AGENT,
            retries={
                'max_attempts': 3,
                'mode': 'standard'
            }
        )

    def get_region(self) -> str:
        return self.__aws_region

    def get_boto_config(self):
        return self.__boto_config

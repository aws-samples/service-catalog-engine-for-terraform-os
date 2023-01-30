import os

from terraform_runner.CommandManager import CommandManager
from terraform_runner.CustomLogger import CustomLogger


class WorkspaceManager:

    def __init__(self, log: CustomLogger, provisioned_product_descriptor: str):
        """
        Parameters:

        log: CustomLogger
            The object used to write logs
        provisioned_product_descriptor: str
            The descriptor that uniquely identifies a provisioned product, used for naming the workspace directory
        """
        self.__log = log
        self.__command_manager = CommandManager(log)
        home_directory = os.path.expanduser('~')
        self.__workspace_directory = f'{home_directory}/workspaces/{provisioned_product_descriptor}'

    def get_workspace_directory(self):
        return self.__workspace_directory

    def remove_workspace_directory(self):
        self.__command_manager.run_command(['rm', '-f', '-r', self.__workspace_directory])

    def setup_workspace_directory(self):
        # Remove any previous workspace directory  for this provisioned product in case there are old files left over from the last run
        self.remove_workspace_directory()
        os.makedirs(self.__workspace_directory)
        self.__log.info(f'Workspace directory set up: {self.__workspace_directory}')

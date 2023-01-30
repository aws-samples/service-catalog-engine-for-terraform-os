import unittest
from unittest.mock import patch

from terraform_runner.CommandManager import CommandManager
from terraform_runner.WorkspaceManager import WorkspaceManager


class TestWorkspaceManager(unittest.TestCase):

    @patch('terraform_runner.WorkspaceManager.CustomLogger')
    @patch('terraform_runner.WorkspaceManager.os')
    @patch.object(CommandManager, 'run_command')
    def test_setup_workspace_directory_happy_path(self, mock_run_command, mock_os, mock_logger):
        # arrange
        mock_os.path.expanduser.return_value = 'home-dir'
        provisioned_product_descriptor = 'pp-descriptor'

        # act
        workspace_manager = WorkspaceManager(mock_logger, provisioned_product_descriptor)
        workspace_manager.setup_workspace_directory()

        # assert
        mock_run_command.assert_called_once_with(['rm', '-f', '-r', workspace_manager.get_workspace_directory()])
        mock_os.makedirs.assert_called_once_with(workspace_manager.get_workspace_directory())

    @patch('terraform_runner.WorkspaceManager.CustomLogger')
    @patch('terraform_runner.WorkspaceManager.os')
    @patch.object(CommandManager, 'run_command')
    def test_remove_workspace_directory_happy_path(self, mock_run_command, mock_os, mock_logger):
        # arrange
        mock_os.path.expanduser.return_value = 'home-dir'
        provisioned_product_descriptor = 'pp-descriptor'

        # act
        workspace_manager = WorkspaceManager(mock_logger, provisioned_product_descriptor)
        workspace_manager.remove_workspace_directory()

        # assert
        mock_run_command.assert_called_once_with(['rm', '-f', '-r', workspace_manager.get_workspace_directory()])


if __name__ == '__main__':
    unittest.main()

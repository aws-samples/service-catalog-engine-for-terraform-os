import unittest
from unittest.mock import Mock, patch

from terraform_runner.CommandManager import CommandManager

SUCCESS_RETURN_CODE = 0
ERROR_RETURN_CODE = 1


class TestCommandManager(unittest.TestCase):

    @patch('terraform_runner.CommandManager.CustomLogger')
    @patch('terraform_runner.CommandManager.subprocess')
    def test_run_command_happy_path(self, mock_subprocess, mock_logger):
        # arrange
        command_manager = CommandManager(mock_logger)
        command = ['foo', 'bar']
        success_result = Mock()
        success_result.returncode = SUCCESS_RETURN_CODE
        mock_subprocess.run.return_value = success_result

        # act
        command_manager.run_command(command)

        # assert
        mock_subprocess.run.assert_called_once()

    @patch('terraform_runner.CommandManager.CustomLogger')
    @patch('terraform_runner.CommandManager.subprocess')
    def test_run_command_with_error_return_code(self, mock_subprocess, mock_logger):
        # arrange
        command_manager = CommandManager(mock_logger)
        command = ['foo', 'bar']
        error_result = Mock()
        error_result.returncode = ERROR_RETURN_CODE
        error_result.stderr = 'standard error'
        mock_subprocess.run.return_value = error_result

        # act and assert
        with self.assertRaises(RuntimeError) as context:
            command_manager.run_command(command)
        self.assertEqual(context.expected, RuntimeError)
        self.assertTrue(str(context.exception).startswith('standard error'))

    @patch('terraform_runner.CommandManager.CustomLogger')
    @patch('terraform_runner.CommandManager.subprocess')
    def test_run_command_exception_raised(self, mock_subprocess, mock_logger):
        # arrange
        command_manager = CommandManager(mock_logger)
        command = ['foo', 'bar']
        mock_subprocess.run.side_effect = Exception('Something went wrong')

        # act and assert
        with self.assertRaises(RuntimeError):
            command_manager.run_command(command)

    @patch('terraform_runner.CommandManager.CustomLogger')
    @patch('terraform_runner.CommandManager.subprocess')
    def test_run_command_with_error_return_code(self, mock_subprocess, mock_logger):
        # arrange
        command_manager = CommandManager(mock_logger)
        command = ['foo', 'bar']
        error_result = Mock()
        error_result.returncode = ERROR_RETURN_CODE
        error_result.stderr = 'standard error'
        mock_subprocess.run.return_value = error_result

        # act and assert
        with self.assertRaises(RuntimeError) as context:
            command_manager.run_command(command)
        self.assertEqual(context.expected, RuntimeError)
        self.assertTrue(str(context.exception).startswith('standard error'))


if __name__ == '__main__':
    unittest.main()

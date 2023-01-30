import subprocess

from terraform_runner.CustomLogger import CustomLogger

SUCCESS_RETURN_CODE = 0


class CommandManager:

    def __init__(self, log: CustomLogger):
        """
        Parameters:

        log: CustomLogger
            The object used to write logs
        """
        self.__log = log

    def run_command(self, command: list, log_stdout: bool = False):
        """
        Parameters:

        command: list of str
            The command and arguments to run
        log_stdout: bool
            When True, logs the stdout of the command given a successful run. Default is False.
        """
        self.__log.info(f'Runnning command: {command}')

        result = None
        try:
            result = subprocess.run(command, check=False, text=True, capture_output=True)
        except Exception as e:
            raise RuntimeError(f'subprocess.run raise and exception while running command {command}: {e}')

        if result.returncode != SUCCESS_RETURN_CODE:
            raise RuntimeError(result.stderr)

        if log_stdout:
            self.__log.info(result.stdout)

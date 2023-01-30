import logging
import sys


class CustomLogger:
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    __log = logging.getLogger()

    def __init__(self, prefix: str):
        """
        Parameters:

        prefix: str
            A prefix to include in every message logged
        """
        self.__prefix = prefix

    def __format(self, message: str):
        return f'{self.__prefix} {message}'

    def info(self, message: str):
        """Logs an info entry including the prefix and message"""
        self.__log.info(self.__format(message))

    def error(self, message: str):
        """Logs an error entry including the prefix and message"""
        self.__log.error(self.__format(message))

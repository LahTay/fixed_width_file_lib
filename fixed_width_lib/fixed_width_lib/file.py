from fixed_width_lib.logger import Logger
from logging import Handler
from pathlib import Path
from typing import List, Union


class File:
    def __init__(self, filepath: str, mode: str, logger_name: str, handlers_list: List[Handler], formatting: str):
        self.filepath = Path(filepath)
        self.mode = mode
        self.file = None
        self.logger = Logger(logger_name, handlers_list, formatting)

    def open(self):
        """
        Opens the managed file
        """
        try:
            self.file = open(self.filepath, self.mode)
        except (FileNotFoundError, PermissionError, OSError):
            self.logger.log_message(f"Failed to open file '{self.filepath}'", "ERROR", exception=True)

    def is_open(self):
        """
        Checking if the file is open
        :return: Is file open
        """
        return self.file is not None and not self.file.closed

    def close(self):
        """
        Closes the managed file
        """
        if self.file:
            try:
                self.file.close()
            except OSError:
                self.logger.log_message(f"Failed to close file '{self.filepath}", "ERROR", exception=True)

    def delete_file(self):
        """
        Deletes the managed file
        """
        try:
            self.filepath.unlink(missing_ok=True)
        except (PermissionError, IsADirectoryError, OSError):
            self.logger.log_message(f"Couldn't delete the file {self.filepath}", "ERROR", exception=True)

    def set_logger(self, logger_name: str, handlers_list: List[Handler], formatting: str):
        """
        Set a new logger
        :param logger_name: Name of the created logger, could also be an instance of another logger
        :param handlers_list: List with instances of valid handlers
        :param formatting: Formatting as a string
        :return:
        """
        self.logger = Logger(logger_name, handlers_list, formatting)

    def set_logger_level(self, level: Union[int, str]):
        self.logger.set_level(level)

    def __enter__(self):
        """
        Opens the file and returns it, not the File class instance itself!
        :return: Return the instance of the open file
        """
        self.open()
        return self.file

    def __exit__(self, exc_type, exc_value, traceback):
        """
        On exit closes the file
        """
        self.close()


from fixed_width_lib.logger import Logger
from pathlib import Path
from typing import Union

class File:
    def __init__(self, filepath, mode, logger_name, handlers_list, formatting):
        self.filepath = Path(filepath)
        self.mode = mode
        self.file = None
        self.logger = Logger(logger_name, handlers_list, formatting)

    def open(self):
        try:
            self.file = open(self.filepath, self.mode)
        except (FileNotFoundError, PermissionError, OSError):
            self.logger.log_message(f"Failed to open file '{self.filepath}'", "ERROR", exception=True)

    def is_open(self):
        """
        Checking if the file is open in any way by using a bit of hacking and trying to rename it to the same name
        if it succeeds then it's closed, if there's an error then it's opened
        TODO: Might need to be changed
        :return: Is file open
        """
        try:
            self.filepath.rename(self.filepath)
            return False
        except (OSError, PermissionError):
            return True

    def close(self):
        if self.file:
            try:
                self.file.close()
            except OSError:
                self.logger.log_message(f"Failed to close file '{self.filepath}", "ERROR", exception=True)

    def delete_file(self):
        try:
            self.filepath.unlink(missing_ok=True)
        except (PermissionError, IsADirectoryError, OSError):
            self.logger.log_message(f"Couldn't delete the file {self.filepath}", "ERROR", exception=True)

    def set_logger_level(self, level: Union[int, str]):
        self.logger.set_level(level)

    def __enter__(self):
        self.open()
        return self.file

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


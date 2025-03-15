from fixed_width_lib.logger import Logger
from logging import Handler
from pathlib import Path
from typing import List, Union, IO


class File:
    def __init__(self, filepath: str, logger: Logger, create_if_missing=False):
        self.filepath = Path(filepath)
        self.mode = "r+"  # As the _file has to work for both writing and reading this is the only available mode
        self.newline = ""  # Has to be set as otherwise each write will insert an endline character
        self._file = None
        self.logger = logger
        self.create_if_missing = create_if_missing

    def get_file(self) -> IO[str]:
        """Returns the _file handle."""
        return self._file

    def open(self):
        """
        Assigns and opens the managed _file
        """
        if self._file is None or self._file.closed:
            try:
                if self.create_if_missing and not self.filepath.exists():
                    self.logger.log_message(f"File '{self.filepath}' not found. Creating a new empty file.", "INFO")
                    self.filepath.touch()

                self._file = open(self.filepath, self.mode, newline=self.newline)
                self.logger.log_message(f"File opened: {self.filepath}", "INFO")
            except (FileNotFoundError, PermissionError, OSError):
                self.logger.log_message(f"Failed to open _file '{self.filepath}'", "ERROR", exception=True)

    def close(self):
        """
        Closes the managed _file and sets the _file variable to None (_file needs to be open() again)
        """
        if self._file and not self._file.closed:
            try:
                self._file.close()
                self._file = None
                self.logger.log_message(f"File closed: {self.filepath}", "INFO")
            except OSError:
                self.logger.log_message(f"Failed to close _file '{self.filepath}", "ERROR", exception=True)

    def set_file(self, filepath: str | Path):
        """
        Allows changing the _file dynamically. After setting it, it still needs to be open
        """
        self.filepath = Path(filepath)
        self.close()

    def set_logger_level(self, level: Union[int, str]):
        self.logger.set_level(level)

    def __enter__(self) -> "File":
        """
        Opens the _file and returns it, not the File class instance itself!
        :return: Return the instance of the open _file
        """
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        On exit closes the _file
        """
        self.close()


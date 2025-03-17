from pathlib import Path
from typing import Union, IO

from fixed_width_lib.logger import Logger


class File:
    def __init__(self, filepath: str, logger: Logger, create_if_missing=False) -> None:
        self.filepath = Path(filepath)
        # As the _file has to work for both writing and reading this is the
        # only available mode
        self.mode = "r+"
        self.newline = ""  # Has to be set as otherwise each write will insert an endline character
        self._file = None
        self.logger = logger
        self.create_if_missing = create_if_missing

    def get_file(self) -> IO[str]:
        """
        Returns the currently managed file handle.

        :return: File handle.
        """
        return self._file

    def open(self) -> None:
        """
        Opens the managed file. If the file does not exist and `create_if_missing` is True, a new empty file is created.
        """
        if self._file is None or self._file.closed:
            try:
                if self.create_if_missing and not self.filepath.exists():
                    self.logger.log_message(
                        f"File '{self.filepath}' not found. Creating a new empty file.", "INFO")
                    self.filepath.touch()

                self._file = open(
                    self.filepath, self.mode, newline=self.newline)
                self.logger.log_message(
                    f"File opened: {self.filepath}", "INFO")
            except (FileNotFoundError, PermissionError, OSError):
                self.logger.log_message(
                    f"Failed to open file '{self.filepath}'",
                    "ERROR",
                    exception=True)

    def close(self) -> None:
        """
        Closes the managed file and resets the file handle to None.
        """
        if self._file and not self._file.closed:
            try:
                self._file.close()
                self._file = None
                self.logger.log_message(
                    f"File closed: {self.filepath}", "INFO")
            except OSError:
                self.logger.log_message(
                    f"Failed to close _file '{self.filepath}",
                    "ERROR",
                    exception=True)

    def set_file(self, filepath: str | Path) -> None:
        """
        Allows changing the _file dynamically. After setting it, it still needs to be open
        """
        self.filepath = Path(filepath)
        self.close()

    def set_logger_level(self, level: Union[int, str]) -> None:
        """
        Sets the logging level for the logger associated with this file.
        """
        self.logger.set_level(level)

    def __enter__(self) -> "File":
        """
        Opens the file when entering a context manager.

        :return: The instance of the File class with the file opened.
        """
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """
        Closes the file when exiting a context manager.

        :param exc_type: The type of exception raised (if any).
        :param exc_value: The exception instance (if any).
        :param traceback: The traceback of the exception (if any).
        """
        self.close()

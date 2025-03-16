from enum import Enum
import logging
from logging import handlers
from typing import List, Union


class LogHandler(Enum):
    """
    Those handlers should be all you'll ever need, but you can always add new ones here if needed
    Convenience enum, so you don't have to import logging in every _file just get the .value and instantiate it
    Some handlers require a _file path as an argument
    """
    STREAM = logging.StreamHandler  # Writes to console
    FILE = logging.FileHandler  # Standard writes to _file
    NULL = logging.NullHandler  # Not logging anything
    # Logs _file and after a certain _file size renames it and creates new one
    ROTATING = handlers.RotatingFileHandler
    # Changes _file after fixed time intervals (daily, weekly etc.)
    TIMED_ROTATING = handlers.TimedRotatingFileHandler
    # Sends logs to a queue - useful for multi-threaded apps
    QUEUE = handlers.QueueHandler
    # Stores logs in memory and only writes after a condition is met
    MEMORY = handlers.MemoryHandler
    HTTP = handlers.HTTPHandler  # Wends logs to an HTTP server
    SOCKET = handlers.SocketHandler  # Sends logs over a network using TCP


class Logger:
    """
    Storage class for all logging purposes including the logger, handler, formatter or others
    It was necessary to make it a stored class because otherwise any changed logging level could also change level
    of logging of libraries that have logging set up globally.

    It is necessary to explicitly set the logging level otherwise default logging library level will be used
    Not setting it up won't cause errors though.
    """

    def __init__(self,
                 logger_name,
                 handlers: List[logging.Handler],
                 formatting: str):
        self.logger = logging.getLogger(logger_name)
        self.logger.propagate = False
        if self.logger.handlers:  # Prevents multiple handlers being added to this logger on creation
            return
        if not handlers:
            raise ValueError(
                f"Logger has to have at least one handler on creation")
        formatter = logging.Formatter(formatting)
        for handler in handlers:
            if not isinstance(handler, logging.Handler):
                raise TypeError(
                    f"Invalid handler type: {handler}. Must be a logging.Handler instance.")

            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        self.log_message("Logger properly set", "INFO")

    def set_level(self, level: Union[str, int]):
        """
        Set the level of the logger itself
        :param level: One of the levels from the logging module as either the string or the int representation
        :return: None
        """
        resolved_level = self._resolve_level(level)
        if resolved_level is None:
            current_level = logging.getLevelName(
                self.logger.getEffectiveLevel())
            self.logger.error(
                f"Invalid log level {level}. Level not changed from {current_level}")
            return
        self.logger.setLevel(resolved_level)
        self.log_message(
            f"Local logging level set to {logging.getLevelName(resolved_level)}",
            "INFO")

    def set_global_level(self, level: Union[str, int]):
        """
        Set the global level of the logging module (useful if other libraries also use logging)
        :param level: One of the levels from the logging module as either the string or the int representation
        :return: None
        """
        resolved_level = self._resolve_level(level)
        if self._resolve_level(level) is None:
            current_level = logging.getLevelName(
                logging.getLogger().getEffectiveLevel())
            self.logger.error(
                f"Invalid log level {level}. Level not changed from {current_level}")
            return
        logging.basicConfig(level=resolved_level)
        self.log_message(
            f"Global logging level set to {logging.getLevelName(resolved_level)}",
            "INFO")

    def log_message(self, message, level, exception=False):
        resolved = self._resolve_level(level)
        if resolved is not None:
            self.logger.log(resolved, message, exc_info=exception)
        else:
            self.logger.error(
                f"Invalid log level {level} Message was not logged properly: {message}")

    def change_handlers(self,
                        new_handlers: List[logging.Handler],
                        new_format: Union[str,
                                          None]):
        """
        Replaces all handlers by removing old ones and adding new handlers

        :param new_handlers: List of new logging.Handler instances
        :param new_format: Either a string indicating the new formatting or None if old formatting is to be used
        :return:
        """

        # First check if the list is good so handlers aren't incorrectly
        # removed
        if not new_handlers:
            self.logger.error(
                "No new handlers in list. Handlers list cannot be empty. If you wish to not log anything"
                "use logging.NullHandler")
            return
        for handler in new_handlers:
            if not isinstance(handler, logging.Handler):
                self.logger.error(f"Invalid handler type: {handler}."
                                  f" Must be a logging.Handler instance.")
                return
        if new_format is None:
            formatter = self.logger.handlers[0].formatter
        else:
            formatter = logging.Formatter(new_format)

        self.logger.handlers.clear()
        for handler in new_handlers:
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _resolve_level(self, level: Union[str, int]):
        """
        Resolves the input level into the correct logging level

        :param level: Either an int or a string showcasing the correct logging level
        :return: Returns the level itself if the level exists otherwise None
        """
        level_name = logging.getLevelName(
            level)  # Converts between string and int or returns "Level {name}"
        if isinstance(level_name, str):
            if level_name.startswith("Level "):
                return None
            return level
        return level_name

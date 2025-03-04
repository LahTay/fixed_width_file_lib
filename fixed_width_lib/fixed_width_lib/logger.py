import logging
from typing import List, Union

class Logger:
    """
    Storage class for all logging purposes including the logger, handler, formatter or others
    It was necessary to make it a stored class because otherwise any changed logging level could also change level
    of logging of libraries that have logging set up globally.

    It is necessary to explicitly set the logging level otherwise default logging library level will be used
    """
    def __init__(self, logger_name, handlers: List, formatting: str):
        self.logger = logging.getLogger(logger_name)
        if self.logger.hasHandlers():  # Prevents multiple handlers being added to the logger on creation
            return
        for handler in handlers:
            handler.setFormatter(logging.Formatter(formatting))
            self.logger.addHandler(handler)

    def set_level(self, level: Union[str, int]):
        if self._resolve_level(level) is None:
            current_level = logging.getLevelName(self.logger.getEffectiveLevel())
            self.logger.error(f"Invalid log level {level} Level not changed from {current_level}")
            return
        self.logger.setLevel(level)

    def log_message(self, message, level):
        if self._resolve_level(level) is not None:
            self.logger.log(level, message)
        else:
            self.logger.error(f"Invalid log level {level} Message was not logged properly: {message}")

    def _resolve_level(self, level: Union[str, int]):
        """
        Resolves the input level into the correct logging level

        :param level: Either an int or a string showcasing the correct logging level
        :return: Returns the level itself if the level exists otherwise None
        """
        level_name = logging.getLevelName(level)  # Converts between string and int or returns "Level {name}"
        if isinstance(level_name, str) and level_name.startswith("Level "):
            return None
        return level

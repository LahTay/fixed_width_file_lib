import logging
import pytest

from fixed_width_lib.logger import Logger, LogHandler


def test_logger_good_initialization(test_output_path):
    """
    Test that a Logger instance initializes correctly with valid handlers.

    :param test_output_path: Path to the directory where test files are stored.
    """
    logging_path = str(test_output_path / "good_initialization.log")
    handlers = [LogHandler.STREAM.value(), LogHandler.FILE.value(logging_path)]
    logger_inst = Logger(
        "good_init_logger",
        handlers,
        "%(asctime)s - %(levelname)s - %(message)s")
    assert len(logger_inst.logger.handlers) == 2


def test_logger_initialization_no_handlers():
    """
    Test that initializing a Logger without handlers raises a ValueError.
    """
    with pytest.raises(ValueError):
        Logger("no_handler_logger", [], "%(message)s")


def test_logger_initialization_invalid_handler():
    """
    Test that initializing a Logger with an invalid handler type raises a TypeError.
    """
    with pytest.raises(TypeError):
        Logger("invalid_handler_logger", [42], "%(message)s")


def test_set_level_valid():
    """
    Test that set_level correctly sets the logger's logging level.

    The logger should update to the specified valid level.
    """
    handlers = [LogHandler.STREAM.value()]
    logger_instance = Logger(
        "test_set_level_valid_logger",
        handlers,
        "%(levelname)s: %(message)s")
    logger_instance.set_level("DEBUG")
    assert logger_instance.logger.getEffectiveLevel() == logging.DEBUG


def test_set_level_invalid(caplog):
    """
    Test that calling set_level with an invalid level logs an error.

    The logger's level should remain unchanged.

    :param caplog: Pytest fixture for capturing log messages.
    """
    handlers = [LogHandler.STREAM.value()]
    logger_instance = Logger(
        "test_set_level_invalid_logger",
        handlers,
        "%(levelname)s: %(message)s")
    original_level = logger_instance.logger.getEffectiveLevel()
    with caplog.at_level(logging.ERROR):
        logger_instance.set_level("INVALID_LEVEL")

    assert any("Invalid log level" in record.message for record in caplog.records)
    assert logger_instance.logger.getEffectiveLevel() == original_level


def test_log_message_valid(caplog):
    """
    Test that a valid log message is recorded when using log_message.

    :param caplog: Pytest fixture for capturing log messages.
    """
    handlers = [LogHandler.STREAM.value()]
    logger_instance = Logger(
        "test_log_message_valid_logger",
        handlers,
        "%(levelname)s: %(message)s")
    logger_instance.set_level("DEBUG")
    test_msg = "This is a test message"
    logger_instance.log_message(test_msg, logging.INFO)
    assert any(test_msg in record.message for record in caplog.records)


def test_log_message_invalid_level(caplog):
    """
    Test that calling log_message with an invalid level logs an error.

    :param caplog: Pytest fixture for capturing log messages.
    """
    handlers = [LogHandler.STREAM.value()]
    logger_instance = Logger(
        "test_log_message_invalid_level_logger",
        handlers,
        "%(levelname)s: %(message)s")
    invalid_level = "NOT_A_LEVEL"
    test_msg = "Message with invalid level"
    with caplog.at_level(logging.ERROR):
        logger_instance.log_message(test_msg, invalid_level)
    assert any("Invalid log level" in record.message for record in caplog.records)


def test_change_handlers_valid(test_output_path):
    """
    Test that change_handlers correctly replaces old handlers with new ones.

    :param test_output_path: Path to the directory where test files are stored.
    """
    handlers = [LogHandler.STREAM.value()]
    logger_instance = Logger(
        "test_change_handlers_valid_logger",
        handlers,
        "%(levelname)s: %(message)s")
    new_log_file = str(test_output_path / "new_log.log")
    new_handlers = [
        LogHandler.STREAM.value(),
        LogHandler.FILE.value(new_log_file)]
    new_format = "%(levelname)s - %(message)s"
    logger_instance.change_handlers(new_handlers, new_format)

    assert len(logger_instance.logger.handlers) == 2
    for handler in logger_instance.logger.handlers:
        assert handler.formatter._fmt == new_format


def test_change_handlers_empty(caplog):
    """
    Test that calling change_handlers with an empty list logs an error.

    :param caplog: Pytest fixture for capturing log messages.
    """
    handlers = [LogHandler.STREAM.value()]
    logger_instance = Logger(
        "test_change_handlers_empty_logger",
        handlers,
        "%(levelname)s: %(message)s")
    with caplog.at_level(logging.ERROR):
        logger_instance.change_handlers([], None)
    assert any(
        "Handlers list cannot be empty" in record.message for record in caplog.records)


def test_change_handlers_invalid_handler(caplog):
    """
    Test that passing an invalid handler type in change_handlers logs an error.

    :param caplog: Pytest fixture for capturing log messages.
    """
    handlers = [LogHandler.STREAM.value()]
    logger_instance = Logger(
        "test_change_handlers_invalid_handler_logger",
        handlers,
        "%(levelname)s: %(message)s")
    invalid_handler = 42
    with caplog.at_level(logging.ERROR):
        logger_instance.change_handlers([invalid_handler], None)
    assert any(
        "Invalid handler type" in record.message for record in caplog.records)

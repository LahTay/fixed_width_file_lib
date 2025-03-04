import logging
import pytest
from fixed_width_lib.logger import Logger, LogHandler



def test_logger_good_initialization(test_output_path):
    logging_path = str(test_output_path / "good_initialization.log")
    handlers = [LogHandler.STREAM.value(), LogHandler.FILE.value(logging_path)]
    logger_inst = Logger("good_init_logger", handlers, "%(asctime)s - %(levelname)s - %(message)s")
    assert len(logger_inst.logger.handlers) == 2

def test_logger_initialization_no_handlers():
    with pytest.raises(ValueError):
        Logger("no_handler_logger", [], "%(message)s")

def test_logger_initialization_invalid_handler():
    with pytest.raises(TypeError):
        Logger("invalid_handler_logger", [42], "%(message)s")

def test_set_level_valid():
    handlers = [LogHandler.STREAM.value()]
    logger_instance = Logger("test_set_level_valid_logger", handlers, "%(levelname)s: %(message)s")
    logger_instance.set_level("DEBUG")
    assert logger_instance.logger.getEffectiveLevel() == logging.DEBUG

def test_set_level_invalid(caplog):
    """
    Tests that calling set_level with an invalid level logs an error and leaves the level unchanged.
    """
    handlers = [LogHandler.STREAM.value()]
    logger_instance = Logger("test_set_level_invalid_logger", handlers, "%(levelname)s: %(message)s")
    original_level = logger_instance.logger.getEffectiveLevel()
    with caplog.at_level(logging.ERROR):
        logger_instance.set_level("INVALID_LEVEL")

    assert any("Invalid log level" in record.message for record in caplog.records)
    assert logger_instance.logger.getEffectiveLevel() == original_level

def test_log_message_valid(caplog):
    """
    Tests that a valid log message is recorded when using log_message.
    """
    handlers = [LogHandler.STREAM.value()]
    logger_instance = Logger("test_log_message_valid_logger", handlers, "%(levelname)s: %(message)s")
    logger_instance.set_level("DEBUG")
    test_msg = "This is a test message"
    logger_instance.log_message(test_msg, logging.INFO)
    # Check that the test message is present in the logs
    assert any(test_msg in record.message for record in caplog.records)

def test_log_message_invalid_level(caplog):
    """
    Tests that calling log_message with an invalid level logs an error message.
    """
    handlers = [LogHandler.STREAM.value()]
    logger_instance = Logger("test_log_message_invalid_level_logger", handlers, "%(levelname)s: %(message)s")
    invalid_level = "NOT_A_LEVEL"
    test_msg = "Message with invalid level"
    with caplog.at_level(logging.ERROR):
        logger_instance.log_message(test_msg, invalid_level)
    assert any("Invalid log level" in record.message for record in caplog.records)


def test_change_handlers_valid(test_output_path):
    """
    Tests that change_handlers correctly replaces old handlers with new ones and updates the formatter.
    """
    handlers = [LogHandler.STREAM.value()]
    logger_instance = Logger("test_change_handlers_valid_logger", handlers, "%(levelname)s: %(message)s")
    new_log_file = str(test_output_path / "new_log.log")
    new_handlers = [LogHandler.STREAM.value(), LogHandler.FILE.value(new_log_file)]
    new_format = "%(levelname)s - %(message)s"
    logger_instance.change_handlers(new_handlers, new_format)

    assert len(logger_instance.logger.handlers) == 2
    for handler in logger_instance.logger.handlers:
        assert handler.formatter._fmt == new_format

def test_change_handlers_empty(caplog):
    """
    Tests that calling change_handlers with an empty list logs an error.
    """
    handlers = [LogHandler.STREAM.value()]
    logger_instance = Logger("test_change_handlers_empty_logger", handlers, "%(levelname)s: %(message)s")
    with caplog.at_level(logging.ERROR):
        logger_instance.change_handlers([], None)
    assert any("Handlers list cannot be empty" in record.message for record in caplog.records)


def test_change_handlers_invalid_handler(caplog):
    """
    Tests that passing an invalid handler type in change_handlers logs an error and aborts the operation.
    """
    handlers = [LogHandler.STREAM.value()]
    logger_instance = Logger("test_change_handlers_invalid_handler_logger", handlers, "%(levelname)s: %(message)s")
    invalid_handler = 42  # Not a valid logging.Handler instance
    with caplog.at_level(logging.ERROR):
        logger_instance.change_handlers([invalid_handler], None)
    assert any("Invalid handler type" in record.message for record in caplog.records)

from pathlib import Path
test = test_logger_good_initialization(Path(__file__).parent / "output")
import pytest
from fixed_width_lib.file import File
from fixed_width_lib.logger import LogHandler
import logging

def test_file_initialization(test_output_path):
    """Test that a File object is properly initialized."""
    file_path = test_output_path / "test_file.txt"
    f = File(str(file_path), "w", "test_logger", [LogHandler.STREAM.value()], "%(message)s")
    assert f is not None
    assert f.filepath == file_path

def test_open_and_close_file(test_output_path):
    """Test that opening and closing a file works as expected."""
    file_path = test_output_path / "test_open_close.txt"
    f = File(str(file_path), "w", "test_logger", [LogHandler.STREAM.value()], "%(message)s")
    assert f.file is None
    f.open()

    assert f.file is not None
    assert f.is_open()

    f.close()
    assert f.file.closed

def test_open_nonexistent_file(test_output_path, caplog):
    """
    Test that attempting to open a nonexistent file in read mode logs an error.
    Since mode "r" on a non-existent file raises an exception, the File.open()
    method should log an error and leave f.file as None.
    """
    file_path = test_output_path / "nonexistent.txt"
    f = File(str(file_path), "r", "test_logger", [LogHandler.STREAM.value()], "%(message)s")
    f.set_logger_level("ERROR")
    f.open()
    assert f.file is None
    error_logged = any("Failed to open file" in record.message for record in caplog.records)
    assert error_logged

def test_delete_file(test_output_path):
    """Test that delete_file removes an existing file."""
    file_path = test_output_path / "to_delete.txt"
    with open(file_path, "w") as temp:
        temp.write("temporary content")
    assert file_path.exists()
    f = File(str(file_path), "r", "test_logger", [LogHandler.STREAM.value()], "%(message)s")
    f.delete_file()
    assert not file_path.exists()

def test_context_manager_usage(test_output_path):
    """
    Test using the File class as a context manager.
    The __enter__ method should open the file and return the file handle.
    """
    file_path = test_output_path / "context_file.txt"
    with File(str(file_path), "w", "test_logger", [LogHandler.STREAM.value()], "%(message)s") as file_handle:
        file_handle.write("test phrase")

    with open(file_path, "r") as f_read:
        content = f_read.read()
    assert content == "test phrase"

def test_set_logger_level(test_output_path, caplog):
    """
    Test that set_logger_level correctly sets the logger's level.
    Log a DEBUG message and verify it appears when the level is set to DEBUG.
    """
    file_path = test_output_path / "test_logger_level.txt"
    f = File(str(file_path), "w", "test_logger", [LogHandler.STREAM.value()], "%(message)s")
    f.set_logger_level("DEBUG")
    f.logger.log_message("debug message", logging.DEBUG)
    debug_logged = any("debug message" in record.message for record in caplog.records)
    assert debug_logged

def test_set_logger(test_output_path, caplog):
    """
    Test that set_logger correctly replaces the existing logger with a new one.
    """
    file_path = test_output_path / "test_set_logger.txt"
    f = File(str(file_path), "w", "initial_logger", [LogHandler.STREAM.value()], "%(message)s")
    f.set_logger("new_logger", [LogHandler.STREAM.value()], "%(levelname)s: %(message)s")
    f.set_logger_level("INFO")
    f.logger.log_message("message from new logger", logging.INFO)
    message_logged = any("message from new logger" in record.message for record in caplog.records)
    assert message_logged


import pytest
from fixed_width_lib.file import File
from fixed_width_lib.logger import LogHandler
import logging


def test_file_initialization(test_output_path, file_stream_logger):
    """Test that a File object is properly initialized."""
    file_path = test_output_path / "test_file.txt"
    f = File(str(file_path), file_stream_logger)
    assert f is not None
    assert f.filepath == file_path


def test_open_and_close_file(test_output_path, file_stream_logger):
    """Test that opening and closing a _file works as expected."""
    file_path = test_output_path / "test_open_close.txt"
    f = File(str(file_path), file_stream_logger)
    f.open()

    assert f.get_file() is not None
    assert not f.get_file().closed

    f.close()
    assert f.get_file() is None  # Check directly if file is not assigned anymore

    f.open()
    assert f.get_file() is not None  # Check if you can open the same file again
    f.close()
    assert f.get_file() is None


def test_open_nonexistent_file(test_output_path, caplog, file_stream_logger):
    """
    Test that attempting to open a nonexistent _file in read mode logs an error.
    Since mode "r" on a non-existent _file raises an exception, the File.open()
    method should log an error and leave f._file as None.
    """
    file_path = test_output_path / "nonexistent.txt"
    f = File(str(file_path), file_stream_logger)
    f.set_logger_level("ERROR")
    f.open()
    assert f.get_file() is None  # Ensure file is not opened
    assert any(
        "Failed to open _file" in record.message for record in caplog.records)


def test_context_manager_usage(test_output_path, file_stream_logger):
    """
    Test using the File class as a context manager.
    The __enter__ method should open the _file and return the _file handle.
    """
    file_path = test_output_path / "context_file.txt"
    with File(str(file_path), file_stream_logger) as f:
        f.get_file().write("test phrase")

    with open(file_path, "r") as f_read:
        content = f_read.read()
    assert content == "test phrase"


def test_set_logger_level(test_output_path, caplog, file_stream_logger):
    """
    Test that set_logger_level correctly sets the logger's level.
    Log a DEBUG message and verify it appears when the level is set to DEBUG.
    """
    file_path = test_output_path / "test_logger_level.txt"
    f = File(str(file_path), file_stream_logger)
    f.set_logger_level("DEBUG")
    f.logger.log_message("debug message", logging.DEBUG)

    assert any("debug message" in record.message for record in caplog.records)


def test_set_file_changes_path(test_output_path, file_stream_logger):
    """Test that set_file correctly updates the file path."""
    file_path1 = test_output_path / "file1.txt"
    file_path2 = test_output_path / "file2.txt"

    f = File(str(file_path1), file_stream_logger)
    assert f.filepath == file_path1

    f.set_file(str(file_path2))
    assert f.filepath == file_path2

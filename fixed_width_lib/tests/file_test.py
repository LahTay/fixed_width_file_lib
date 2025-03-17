import pytest
from fixed_width_lib.file import File


def test_file_initialization(test_output_path, file_stream_logger):
    """
    Test that a File object is properly initialized.

    :param test_output_path: Path object for the test output directory.
    :param file_stream_logger: Logger instance for logging.
    """
    file_path = test_output_path / "test_file.txt"
    f = File(str(file_path), file_stream_logger)
    assert f is not None
    assert f.filepath == file_path


def test_open_and_close_file(test_output_path, file_stream_logger):
    """
    Test opening and closing a file.

    :param test_output_path: Path to the directory where test files are stored.
    :param file_stream_logger: Logger instance with both file and stream handlers.
    """
    file_path = test_output_path / "test_open_close.txt"
    f = File(str(file_path), file_stream_logger)
    f.open()

    assert f.get_file() is not None
    assert not f.get_file().closed

    f.close()
    assert f.get_file() is None

    f.open()
    assert f.get_file() is not None
    f.close()
    assert f.get_file() is None


def test_open_nonexistent_file(test_output_path, caplog, file_stream_logger):
    """
    Test opening a nonexistent file logs an error.

    :param test_output_path: Path to the directory where test files are stored.
    :param caplog: Pytest fixture for capturing log messages.
    :param file_stream_logger: Logger instance with both file and stream handlers.
    """
    file_path = test_output_path / "nonexistent.txt"
    f = File(str(file_path), file_stream_logger)
    f.set_logger_level("ERROR")
    f.open()
    assert f.get_file() is None
    assert any(
        "Failed to open file" in record.message for record in caplog.records)


def test_context_manager_usage(test_output_path, file_stream_logger):
    """
    Test using the File class as a context manager.

    :param test_output_path: Path to the directory where test files are stored.
    :param file_stream_logger: Logger instance with both file and stream handlers.
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

    :param test_output_path: Path to the directory where test files are stored.
    :param caplog: Pytest fixture for capturing log messages.
    :param file_stream_logger: Logger instance with both file and stream handlers.
    """
    file_path = test_output_path / "test_logger_level.txt"
    f = File(str(file_path), file_stream_logger)
    f.set_logger_level("DEBUG")
    f.logger.log_message("debug message", "DEBUG")

    assert any("debug message" in record.message for record in caplog.records)


def test_set_file_changes_path(test_output_path, file_stream_logger):
    """
    Test that set_file correctly updates the file path.

    :param test_output_path: Path to the directory where test files are stored.
    :param file_stream_logger: Logger instance with both file and stream handlers.
    """
    file_path1 = test_output_path / "file1.txt"
    file_path2 = test_output_path / "file2.txt"

    f = File(str(file_path1), file_stream_logger)
    assert f.filepath == file_path1

    f.set_file(str(file_path2))
    assert f.filepath == file_path2

from pathlib import Path
import pytest
import sys
from fixed_width_lib.logger import Logger, LogHandler
from fixed_width_lib.transaction_manager import TransactionManager


@pytest.fixture
def test_data_path():
    """
    Returns the path to the test data directory.

    :return: Path object pointing to the test data directory.
    """
    return Path(__file__).parent / "test_data"


@pytest.fixture
def test_logging_path():
    """
    Returns the path to the logging directory for test logs.

    :return: Path object pointing to the logging directory.
    """
    return Path(__file__).parent / "logging"


@pytest.fixture
def test_output_path():
    """
    Creates and returns the path to the output directory for test results.

    :return: Path object pointing to the output directory.
    """
    output_path = Path(__file__).parent / "output"
    output_path.mkdir(exist_ok=True)
    return output_path


@pytest.fixture
def example_file(test_data_path: Path) -> Path:
    """
    Returns the path to an example test file stored in the test data directory.

    :param test_data_path: Path object representing the test data directory.
    :return: Path object pointing to the example file.
    """
    return test_data_path / "example_file"


@pytest.fixture
def file_stream_logger():
    """
    Creates a logger that writes log messages to both a test log file and the console.
    The log file is stored in the "logs" directory under the project's root.

    :return: Logger instance with both file and stream handlers.
    """
    log_file = Path(__file__).parent.parent / "logs" / "tests.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    return Logger("test_logger",
                  [LogHandler.FILE.value(str(log_file)),
                   LogHandler.STREAM.value()],
                  "%(asctime)s - %(name)s - %(levelname)s - %(message)s")


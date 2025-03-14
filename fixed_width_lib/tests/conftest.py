from pathlib import Path
import pytest
import sys
from fixed_width_lib.logger import Logger, LogHandler


@pytest.fixture
def test_data_path():
    return Path(__file__).parent / "test_data"


@pytest.fixture
def test_logging_path():
    return Path(__file__).parent / "logging"


@pytest.fixture
def test_output_path():
    output_path = Path(__file__).parent / "output"
    output_path.mkdir(exist_ok=True)
    return output_path


@pytest.fixture
def example_file(test_data_path: Path) -> Path:
    # Assumes the sample _file is located at test_data/example_file
    return test_data_path / "example_file"


@pytest.fixture
def stream_logger():
    return Logger("test_logger",
                  [LogHandler.STREAM.value()],
                  "%(asctime)s - %(name)s - %(levelname)s - %(message)s")


@pytest.fixture
def file_logger():
    log_file = Path(__file__).parent.parent / "logs" / "tests.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    return Logger("test_logger",
                  [LogHandler.FILE.value(str(log_file))],
                  "%(asctime)s - %(name)s - %(levelname)s - %(message)s")


@pytest.fixture
def file_stream_logger():
    log_file = Path(__file__).parent.parent / "logs" / "tests.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    return Logger("test_logger",
                  [LogHandler.FILE.value(str(log_file)), LogHandler.STREAM.value()],
                  "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

from pathlib import Path
import pytest
import sys


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
    # Assumes the sample file is located at test_data/example_file
    return test_data_path / "example_file"
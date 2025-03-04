from pathlib import Path
import pytest
import sys

# For the pytest to find the local module I could move conftest to the main folder but that's ugly so I will do this:
# It will add the project root to sys.path
# sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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


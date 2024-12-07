
import sys
import os
from pathlib import Path
import pytest

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, project_root)

# Configure test settings
os.environ["ENV"] = "test"
os.environ["PYTEST_CURRENT_TEST"] = "true"

@pytest.fixture(scope="session")
def temp_output_dir(tmp_path_factory):
    """Create a temporary directory for test outputs"""
    return tmp_path_factory.mktemp("test_output")
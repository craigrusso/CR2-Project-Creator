import os
import pytest
import tempfile
from pathlib import Path

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)

@pytest.fixture
def test_file(temp_dir):
    """Create a test file with some content."""
    file_path = temp_dir / "test_file.txt"
    file_path.write_text("Test content")
    return file_path 
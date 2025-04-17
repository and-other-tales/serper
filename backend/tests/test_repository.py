import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from exceptions.api_exceptions import APIError


@pytest.fixture
def source_fetcher():
    """Fixture to create a SourceFetcher with mocked client."""
    from content.fetcher import SourceFetcher

    mock_client = MagicMock()
    return SourceFetcher(token=None, client=mock_client)


def test_process_file_success(source_fetcher, tmp_path):
    """Test _process_file when the file is successfully fetched and saved."""
    source = "test_source"
    base_dir = tmp_path
    file_info = {
        "name": "test_file.txt",
        "path": "docs/test_file.txt",
        "sha": "abc123",
        "size": 1024,
        "url": "https://example.com/docs/test_file.txt",
    }
    file_content = "This is a test file."

    # Mock the client to return file content
    source_fetcher.client.get_file.return_value = file_content

    result = source_fetcher._process_file(source, file_info, base_dir)

    # Verify the file was saved correctly
    saved_file = Path(base_dir) / file_info["name"]
    assert saved_file.exists()
    assert saved_file.read_text() == file_content

    # Check required fields in the result
    assert result["name"] == file_info["name"]
    assert result["path"] == file_info["path"]
    assert result["local_path"] == str(saved_file)
    assert result["size"] == file_info["size"]
    assert result["url"] == file_info["url"]
    assert result["sha"] == file_info["sha"]
    # These extra fields are fine
    assert result["source"] == source


def test_process_file_api_error(source_fetcher, tmp_path):
    """Test _process_file when an APIError occurs."""
    source = "test_source"
    base_dir = tmp_path
    file_info = {
        "name": "test_file.txt",
        "path": "docs/test_file.txt",
        "sha": "abc123",
        "size": 1024,
        "url": "https://example.com/docs/test_file.txt",
    }

    # Mock the client to raise an error
    source_fetcher.client.get_file.side_effect = APIError(
        "API error"
    )

    # Call the method and check that it handles the exception
    result = source_fetcher._process_file(source, file_info, base_dir)

    # Verify the file wasn't saved and the result contains the error
    saved_file = Path(base_dir) / file_info["name"]
    assert not saved_file.exists()
    assert "error" in result
    assert "API error" in result["error"]

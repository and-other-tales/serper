import unittest
import os
import sys
import tempfile
from unittest.mock import MagicMock, patch
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from github.client import GitHubClient, GitHubAPIError
from github.repository import RepositoryFetcher
from github.content_fetcher import ContentFetcher
from utils.llm_client import LLMClient, GitHubInstructionsSchema


class TestGitHubIntegration(unittest.TestCase):
    """Test the GitHub integration functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock GitHub client
        self.mock_client = MagicMock(spec=GitHubClient)
        
        # Create temp directory for cache
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create repository fetcher with mock client
        self.repo_fetcher = RepositoryFetcher(client=self.mock_client)
        self.repo_fetcher.cache_dir = Path(self.temp_dir.name)
        
        # Create content fetcher with mock repository fetcher
        self.content_fetcher = ContentFetcher()
        self.content_fetcher.repo_fetcher = self.repo_fetcher
        
        # Sample repository data
        self.sample_repo = {
            "id": 123456789,
            "name": "test-repo",
            "full_name": "test-user/test-repo",
            "owner": {"login": "test-user"},
            "html_url": "https://github.com/test-user/test-repo",
            "description": "A test repository",
            "default_branch": "main"
        }
        
        # Sample repository structure
        self.sample_structure = {
            "total_files": 5,
            "relevant_files": 3,
            "relevant_paths": ["docs", "examples"],
            "structure": {
                "docs": {
                    "files": [
                        {"name": "README.md", "path": "docs/README.md", "sha": "abc123", "size": 1024}
                    ]
                },
                "examples": {
                    "files": [
                        {"name": "example.py", "path": "examples/example.py", "sha": "def456", "size": 2048},
                        {"name": "config.json", "path": "examples/config.json", "sha": "ghi789", "size": 512}
                    ]
                }
            }
        }

    def tearDown(self):
        """Tear down test fixtures."""
        self.temp_dir.cleanup()

    @patch('github.client.requests.get')
    def test_fetch_repository(self, mock_get):
        """Test fetching a repository."""
        # Configure mock to return sample repo data
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_repo
        mock_get.return_value = mock_response
        
        # Configure mock client to return sample repo
        self.mock_client.get_repository.return_value = self.sample_repo
        
        # Configure mock client for structure scan
        self.mock_client.scan_repository_structure.return_value = self.sample_structure
        
        # Configure mock client for file content
        self.mock_client.get_repository_file.return_value = "Sample file content"
        
        # Set up progress callback mock
        mock_callback = MagicMock()
        
        # Call the fetch method
        result = self.content_fetcher.fetch_single_repository(
            "https://github.com/test-user/test-repo",
            progress_callback=mock_callback
        )
        
        # Check that repository was fetched correctly
        self.mock_client.get_repository.assert_called_once_with("test-user", "test-repo")
        
        # Check that structure was scanned
        self.mock_client.scan_repository_structure.assert_called_once_with(
            "test-user", "test-repo", "main"
        )
        
        # Check that progress callback was called
        mock_callback.assert_called()
        
        # Check that we got file content back
        self.assertIsNotNone(result)
        self.assertGreater(len(result), 0)

    @patch('github.content_fetcher.ContentFetcher.get_github_instructions')
    def test_ai_guided_repository_fetch(self, mock_get_instructions):
        """Test fetching a repository with AI guidance."""
        # Configure mock client to return sample repo
        self.mock_client.get_repository.return_value = self.sample_repo
        
        # Configure mock client for structure scan
        self.mock_client.scan_repository_structure.return_value = self.sample_structure
        
        # Configure mock client for file content
        self.mock_client.get_repository_file.return_value = "Sample file content"
        
        # Configure mock for AI instructions
        mock_instructions = {
            "file_patterns": ["*.md", "*.json"],
            "exclude_patterns": ["test_*"],
            "max_files": 10,
            "include_directories": ["docs"],
            "exclude_directories": ["tests"],
            "extraction_goal": "documentation",
            "priority_content": ["guide", "tutorial"]
        }
        mock_get_instructions.return_value = mock_instructions
        
        # Set up progress callback mock
        mock_callback = MagicMock()
        
        # Call the fetch method with AI guidance
        result = self.content_fetcher.fetch_single_repository(
            "https://github.com/test-user/test-repo",
            progress_callback=mock_callback,
            user_instructions="I need all documentation files",
            use_ai_guidance=True
        )
        
        # Check that AI instructions were requested
        mock_get_instructions.assert_called_once_with(
            "I need all documentation files", 
            "https://github.com/test-user/test-repo"
        )
        
        # Check that repository was fetched correctly
        self.mock_client.get_repository.assert_called_once_with("test-user", "test-repo")
        
        # Check that progress callback was called
        mock_callback.assert_called()
        
        # Check that we got file content back
        self.assertIsNotNone(result)
        
        # Check that file patterns were set on the repository fetcher
        self.assertEqual(self.repo_fetcher.file_patterns, mock_instructions["file_patterns"])
        self.assertEqual(self.repo_fetcher.exclude_patterns, mock_instructions["exclude_patterns"])
        self.assertEqual(self.repo_fetcher.include_directories, mock_instructions["include_directories"])
        self.assertEqual(self.repo_fetcher.exclude_directories, mock_instructions["exclude_directories"])
        self.assertEqual(self.repo_fetcher.priority_content, mock_instructions["priority_content"])

    @patch('utils.llm_client.LLMClient.generate_github_instructions')
    def test_llm_client_github_instructions(self, mock_generate):
        """Test generating GitHub instructions with LLM client."""
        # Configure mock instructions
        mock_instructions = {
            "file_patterns": ["*.md", "*.json"],
            "exclude_patterns": ["test_*"],
            "max_files": 10,
            "include_directories": ["docs"],
            "exclude_directories": ["tests"],
            "extraction_goal": "documentation",
            "priority_content": ["guide", "tutorial"]
        }
        mock_generate.return_value = mock_instructions
        
        # Create LLM client
        llm_client = LLMClient()
        
        # Test generating GitHub instructions
        result = llm_client.generate_github_instructions(
            "I need all documentation files",
            "https://github.com/test-user/test-repo"
        )
        
        # Check that mock was called
        mock_generate.assert_called_once_with(
            "I need all documentation files",
            "https://github.com/test-user/test-repo"
        )
        
        # Check returned instructions
        self.assertEqual(result, mock_instructions)
        self.assertEqual(result["file_patterns"], ["*.md", "*.json"])
        self.assertEqual(result["extraction_goal"], "documentation")

    def test_repository_fetcher_filtering(self):
        """Test file filtering based on AI guidance."""
        # Set up AI guidance settings
        self.repo_fetcher.file_patterns = ["*.md", "*.json"]
        self.repo_fetcher.exclude_patterns = ["test_*"]
        self.repo_fetcher.include_directories = ["docs"]
        self.repo_fetcher.exclude_directories = ["tests"]
        
        # Test file pattern matching
        self.assertTrue(self.repo_fetcher._is_text_file("README.md"))
        self.assertTrue(self.repo_fetcher._is_text_file("config.json"))
        self.assertFalse(self.repo_fetcher._is_text_file("script.py"))  # Not in patterns
        self.assertFalse(self.repo_fetcher._is_text_file("test_file.md"))  # In exclude
        
        # Test directory filtering
        self.assertTrue(self.repo_fetcher._is_relevant_folder("docs"))
        self.assertFalse(self.repo_fetcher._is_relevant_folder("tests"))  # In exclude
        self.assertFalse(self.repo_fetcher._is_relevant_folder("src"))  # Not in include

    def test_download_queued_files_with_max_files(self):
        """Test downloading queued files with max_files limit."""
        # Add more files than max_files
        self.repo_fetcher.download_queue.reset()
        
        # Add test files to queue
        for i in range(10):
            self.repo_fetcher.download_queue.add_file({
                "owner": "test-user",
                "repo": "test-repo",
                "path": f"file{i}.md",
                "branch": "main",
                "local_path": f"/tmp/file{i}.md"
            })
        
        # Configure mock client for file content
        self.mock_client.get_repository_file.return_value = "Sample file content"
        
        # Patch file write to avoid actually writing files
        with patch('pathlib.Path.write_text') as mock_write, \
             patch('pathlib.Path.parent.mkdir') as mock_mkdir:
            
            # Set max_files to less than total files
            max_files = 5
            
            # Call download function with max_files
            result = self.repo_fetcher._download_queued_files(
                "test-user", "test-repo", "main", max_files=max_files
            )
            
            # Check that only max_files files were downloaded
            self.assertEqual(len(result), max_files)
            self.assertEqual(mock_write.call_count, max_files)


if __name__ == '__main__':
    unittest.main()
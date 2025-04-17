"""
GitHub API integration module for othertales Serper.
"""

# Make imports easier by exposing key classes
from .client import GitHubClient, GitHubAPIError, RateLimitError
from .repository import RepositoryFetcher
from .content_fetcher import ContentFetcher
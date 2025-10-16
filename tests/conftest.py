"""Pytest configuration and fixtures."""

import pytest
from unittest.mock import Mock
from src.config import Settings


@pytest.fixture
def test_settings():
    """Provide test settings that don't require environment variables."""
    return Settings(
        jira_base_url="https://test.atlassian.net",
        jira_email="test@example.com",
        jira_api_token="test-token",
        confluence_base_url="https://test.atlassian.net",
        confluence_email="test@example.com",
        confluence_api_token="test-token",
        bitbucket_workspace="test-workspace",
        bitbucket_repo_slug="test-repo",
        bitbucket_username="test-user",
        bitbucket_app_password="test-password",
        openai_api_key="test-key",
        dry_run=True
    )


@pytest.fixture
def mock_jira_client():
    """Mock Jira client for testing."""
    mock = Mock()
    mock.get_issues_by_fix_version.return_value = []
    mock.get_issues_by_branch.return_value = []
    mock.get_issues_by_pr.return_value = []
    mock.close.return_value = None
    return mock


@pytest.fixture
def mock_bitbucket_client():
    """Mock Bitbucket client for testing."""
    mock = Mock()
    mock.get_pull_requests_for_branch.return_value = []
    mock.get_commits_for_branch.return_value = []
    mock.branch_exists.return_value = True
    mock.close.return_value = None
    return mock


@pytest.fixture
def mock_confluence_client():
    """Mock Confluence client for testing."""
    mock = Mock()
    mock.get_release_notes_page.return_value = None
    mock.get_pages_by_labels.return_value = []
    mock.search_pages.return_value = []
    mock.close.return_value = None
    return mock

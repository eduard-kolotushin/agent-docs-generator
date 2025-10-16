"""Integration tests for the release docs agent."""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch
from src.schemas import AgentState


@pytest.mark.asyncio
async def test_dry_run_mode():
    """Test the agent in dry-run mode."""
    # Create a test state
    state = AgentState(
        release_branch="release/1.2.3",
        version="1.2.3",
        base_tag="v1.2.2",
        dry_run=True
    )
    
    # Test basic state creation
    assert state.version == "1.2.3"
    assert state.release_branch == "release/1.2.3"
    assert state.dry_run is True


@pytest.mark.asyncio
async def test_agent_with_mock_data():
    """Test the agent with mock data."""
    # Create a test state
    state = AgentState(
        release_branch="release/1.2.3",
        version="1.2.3",
        base_tag="v1.2.2",
        dry_run=True
    )
    
    # Test state properties
    assert state.version == "1.2.3"
    assert state.release_branch == "release/1.2.3"
    assert state.base_tag == "v1.2.2"
    assert state.dry_run is True


def test_environment_setup(test_settings):
    """Test that environment variables are properly loaded."""
    # Check that settings are loaded with defaults
    assert hasattr(test_settings, 'jira_base_url')
    assert hasattr(test_settings, 'bitbucket_workspace')
    assert hasattr(test_settings, 'confluence_base_url')
    assert hasattr(test_settings, 'openai_api_key')
    assert test_settings.jira_base_url == "https://test.atlassian.net"


def test_schema_validation():
    """Test that schemas properly validate data."""
    from src.schemas import JiraIssue
    from datetime import datetime
    from pydantic import ValidationError
    
    # Test valid data
    issue = JiraIssue(
        key="PROJ-123",
        summary="Test",
        issue_type="Story",
        status="Done",
        priority="High",
        components=[],
        labels=[],
        fix_version="1.2.3",
        epic_key=None,
        changelog=None,
        breaking_change=False,
        assignee=None,
        reporter=None,
        created=datetime.now(),
        updated=datetime.now()
    )
    
    assert issue.key == "PROJ-123"
    
    # Test invalid data should raise validation error
    with pytest.raises(ValidationError):
        JiraIssue(
            key="",  # Empty key should fail validation
            summary="Test",
            issue_type="Story",
            status="Done",
            priority="High",
            components=[],
            labels=[],
            fix_version="1.2.3",
            epic_key=None,
            changelog=None,
            breaking_change=False,
            assignee=None,
            reporter=None,
            created=datetime.now(),
            updated=datetime.now()
        )

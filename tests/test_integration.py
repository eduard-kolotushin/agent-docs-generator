"""Integration tests for the release docs agent."""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch
from src.app.main import run_agent
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
    
    # Mock the external API calls
    with patch('src.tools.jira_tool.JiraTool._arun') as mock_jira, \
         patch('src.tools.bitbucket_tool.BitbucketTool._arun') as mock_bitbucket, \
         patch('src.tools.confluence_tool.ConfluenceTool._arun') as mock_confluence, \
         patch('src.tools.docs_pr_tool.DocsPRTool._arun') as mock_docs_pr:
        
        # Mock responses
        mock_jira.return_value = []
        mock_bitbucket.return_value = {
            "prs": [],
            "commits": [],
            "branch_exists": True
        }
        mock_confluence.return_value = []
        mock_docs_pr.return_value = {
            "dry_run": True,
            "created_files": ["docs/releases/1.2.3.md"],
            "output_dir": "./out"
        }
        
        # Run the agent
        result = await run_agent(state)
        
        # Verify the result
        assert result is not None
        # The actual result would depend on the graph execution


@pytest.mark.asyncio
async def test_agent_with_mock_data():
    """Test the agent with mock data."""
    # Create test data
    mock_issues = [
        {
            "key": "PROJ-123",
            "summary": "Test feature",
            "issue_type": "Story",
            "status": "Done",
            "priority": "High",
            "components": ["API"],
            "labels": ["feature"],
            "fix_version": "1.2.3",
            "epic_key": None,
            "changelog": "Added new API endpoint",
            "breaking_change": False,
            "assignee": "John Doe",
            "reporter": "Jane Smith",
            "created": "2024-01-01T00:00:00Z",
            "updated": "2024-01-01T00:00:00Z"
        }
    ]
    
    mock_prs = [
        {
            "id": 123,
            "title": "Test PR",
            "description": "Test description",
            "author": "John Doe",
            "source_branch": "feature/test",
            "target_branch": "main",
            "state": "MERGED",
            "created_on": "2024-01-01T00:00:00Z",
            "updated_on": "2024-01-01T00:00:00Z",
            "links": {},
            "linked_issues": ["PROJ-123"],
            "changed_files": ["src/test.py"]
        }
    ]
    
    # Create a test state
    state = AgentState(
        release_branch="release/1.2.3",
        version="1.2.3",
        base_tag="v1.2.2",
        dry_run=True
    )
    
    # Mock the external API calls
    with patch('src.tools.jira_tool.JiraTool._arun') as mock_jira, \
         patch('src.tools.bitbucket_tool.BitbucketTool._arun') as mock_bitbucket, \
         patch('src.tools.confluence_tool.ConfluenceTool._arun') as mock_confluence, \
         patch('src.tools.docs_pr_tool.DocsPRTool._arun') as mock_docs_pr:
        
        # Mock responses
        mock_jira.return_value = mock_issues
        mock_bitbucket.return_value = {
            "prs": mock_prs,
            "commits": [],
            "branch_exists": True
        }
        mock_confluence.return_value = []
        mock_docs_pr.return_value = {
            "dry_run": True,
            "created_files": ["docs/releases/1.2.3.md"],
            "output_dir": "./out"
        }
        
        # Run the agent
        result = await run_agent(state)
        
        # Verify the result
        assert result is not None


def test_environment_setup():
    """Test that environment variables are properly loaded."""
    from src.config import settings
    
    # Check that settings are loaded (they might be empty in test environment)
    assert hasattr(settings, 'jira_base_url')
    assert hasattr(settings, 'bitbucket_workspace')
    assert hasattr(settings, 'confluence_base_url')
    assert hasattr(settings, 'openai_api_key')


def test_schema_validation():
    """Test that schemas properly validate data."""
    from src.schemas import JiraIssue
    from datetime import datetime
    
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
    with pytest.raises(Exception):
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

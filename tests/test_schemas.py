"""Tests for schemas."""

import pytest
from datetime import datetime
from src.schemas import JiraIssue, BitbucketPR, BitbucketCommit, ReleaseContext, AgentState


def test_jira_issue_creation():
    """Test JiraIssue creation."""
    issue = JiraIssue(
        key="PROJ-123",
        summary="Test issue",
        issue_type="Story",
        status="Done",
        priority="High",
        components=["API", "UI"],
        labels=["feature", "enhancement"],
        fix_version="1.2.3",
        epic_key="PROJ-100",
        changelog="Added new feature",
        breaking_change=False,
        assignee="John Doe",
        reporter="Jane Smith",
        created=datetime.now(),
        updated=datetime.now()
    )
    
    assert issue.key == "PROJ-123"
    assert issue.summary == "Test issue"
    assert issue.issue_type == "Story"
    assert issue.components == ["API", "UI"]
    assert issue.breaking_change is False


def test_bitbucket_pr_creation():
    """Test BitbucketPR creation."""
    pr = BitbucketPR(
        id=123,
        title="Test PR",
        description="Test description",
        author="John Doe",
        source_branch="feature/test",
        target_branch="main",
        state="MERGED",
        created_on=datetime.now(),
        updated_on=datetime.now(),
        links={"html": {"href": "https://example.com/pr/123"}},
        linked_issues=["PROJ-123"],
        changed_files=["src/test.py", "docs/test.md"]
    )
    
    assert pr.id == 123
    assert pr.title == "Test PR"
    assert pr.author == "John Doe"
    assert pr.linked_issues == ["PROJ-123"]


def test_release_context_creation():
    """Test ReleaseContext creation."""
    context = ReleaseContext(
        version="1.2.3",
        release_branch="release/1.2.3",
        base_tag="v1.2.2"
    )
    
    assert context.version == "1.2.3"
    assert context.release_branch == "release/1.2.3"
    assert context.base_tag == "v1.2.2"
    assert context.jira_issues == []
    assert context.bitbucket_prs == []


def test_agent_state_creation():
    """Test AgentState creation."""
    state = AgentState(
        release_branch="release/1.2.3",
        version="1.2.3",
        base_tag="v1.2.2",
        dry_run=True
    )
    
    assert state.release_branch == "release/1.2.3"
    assert state.version == "1.2.3"
    assert state.dry_run is True
    assert state.current_step == "validate_release"

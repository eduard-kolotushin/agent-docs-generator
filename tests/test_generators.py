"""Tests for generators."""

import pytest
from datetime import datetime
from src.generators.release_notes import format_jira_issues, format_bitbucket_prs, format_bitbucket_commits
from src.generators.guide_edits import generate_changelog_entry, plan_component_guide_update
from src.schemas import JiraIssue, BitbucketPR, BitbucketCommit, ReleaseContext


def test_format_jira_issues():
    """Test formatting Jira issues."""
    issues = [
        JiraIssue(
            key="PROJ-123",
            summary="Test feature",
            issue_type="Story",
            status="Done",
            priority="High",
            components=["API"],
            labels=["feature"],
            fix_version="1.2.3",
            epic_key=None,
            changelog="Added new API endpoint",
            breaking_change=False,
            assignee="John Doe",
            reporter="Jane Smith",
            created=datetime.now(),
            updated=datetime.now()
        )
    ]
    
    formatted = format_jira_issues(issues)
    
    assert "PROJ-123" in formatted
    assert "Test feature" in formatted
    assert "Story" in formatted
    assert "API" in formatted


def test_format_bitbucket_prs():
    """Test formatting Bitbucket PRs."""
    prs = [
        BitbucketPR(
            id=123,
            title="Test PR",
            description="Test description",
            author="John Doe",
            source_branch="feature/test",
            target_branch="main",
            state="MERGED",
            created_on=datetime.now(),
            updated_on=datetime.now(),
            links={},
            linked_issues=["PROJ-123"],
            changed_files=["src/test.py"]
        )
    ]
    
    formatted = format_bitbucket_prs(prs)
    
    assert "PR #123" in formatted
    assert "Test PR" in formatted
    assert "John Doe" in formatted
    assert "MERGED" in formatted


def test_generate_changelog_entry():
    """Test generating changelog entry."""
    context = ReleaseContext(
        version="1.2.3",
        release_branch="release/1.2.3",
        base_tag="v1.2.2"
    )
    
    # Add some test issues
    context.new_features = [
        JiraIssue(
            key="PROJ-123",
            summary="New feature",
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
    ]
    
    context.bug_fixes = [
        JiraIssue(
            key="PROJ-456",
            summary="Bug fix",
            issue_type="Bug",
            status="Done",
            priority="Medium",
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
    ]
    
    changelog = generate_changelog_entry(context)
    
    assert "## [1.2.3]" in changelog
    assert "### Added" in changelog
    assert "### Fixed" in changelog
    assert "PROJ-123" in changelog
    assert "PROJ-456" in changelog


def test_plan_component_guide_update():
    """Test planning component guide update."""
    context = ReleaseContext(
        version="1.2.3",
        release_branch="release/1.2.3",
        base_tag="v1.2.2"
    )
    
    # Add test issues
    context.jira_issues = [
        JiraIssue(
            key="PROJ-123",
            summary="API improvement",
            issue_type="Story",
            status="Done",
            priority="High",
            components=["api"],
            labels=[],
            fix_version="1.2.3",
            epic_key=None,
            changelog="Improved API performance",
            breaking_change=False,
            assignee=None,
            reporter=None,
            created=datetime.now(),
            updated=datetime.now()
        )
    ]
    
    guide_edit = plan_component_guide_update("api", context)
    
    assert guide_edit is not None
    assert guide_edit.file_path == "docs/api-guide.md"
    assert guide_edit.operation == "update"
    assert "api" in guide_edit.metadata["component"]

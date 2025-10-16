"""Pydantic schemas for the release docs agent."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class JiraIssue(BaseModel):
    """Jira issue data."""
    key: str
    summary: str
    issue_type: str
    status: str
    priority: str
    components: List[str] = Field(default_factory=list)
    labels: List[str] = Field(default_factory=list)
    fix_version: Optional[str] = None
    epic_key: Optional[str] = None
    changelog: Optional[str] = None
    breaking_change: bool = False
    assignee: Optional[str] = None
    reporter: Optional[str] = None
    created: datetime
    updated: datetime


class BitbucketPR(BaseModel):
    """Bitbucket pull request data."""
    id: int
    title: str
    description: Optional[str] = None
    author: str
    source_branch: str
    target_branch: str
    state: str
    created_on: datetime
    updated_on: datetime
    links: Dict[str, Any] = Field(default_factory=dict)
    linked_issues: List[str] = Field(default_factory=list)
    changed_files: List[str] = Field(default_factory=list)


class BitbucketCommit(BaseModel):
    """Bitbucket commit data."""
    hash: str
    message: str
    author: str
    date: datetime
    links: Dict[str, Any] = Field(default_factory=dict)
    changed_files: List[str] = Field(default_factory=list)


class ConfluencePage(BaseModel):
    """Confluence page data."""
    id: str
    title: str
    content: str
    space_key: str
    version: int
    created: datetime
    updated: datetime
    labels: List[str] = Field(default_factory=list)
    attachments: List[Dict[str, Any]] = Field(default_factory=list)


class DocEdit(BaseModel):
    """Documentation edit operation."""
    file_path: str
    operation: str  # "create", "update", "delete"
    content: Optional[str] = None
    old_content: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReleaseContext(BaseModel):
    """Aggregated context for a release."""
    version: str
    release_branch: str
    base_tag: Optional[str] = None
    
    # Gathered data
    jira_issues: List[JiraIssue] = Field(default_factory=list)
    bitbucket_prs: List[BitbucketPR] = Field(default_factory=list)
    bitbucket_commits: List[BitbucketCommit] = Field(default_factory=list)
    confluence_pages: List[ConfluencePage] = Field(default_factory=list)
    
    # Analysis results
    affected_components: List[str] = Field(default_factory=list)
    breaking_changes: List[JiraIssue] = Field(default_factory=list)
    new_features: List[JiraIssue] = Field(default_factory=list)
    bug_fixes: List[JiraIssue] = Field(default_factory=list)
    
    # Generated content
    release_notes: Optional[str] = None
    doc_edits: List[DocEdit] = Field(default_factory=list)
    images_to_download: List[Dict[str, str]] = Field(default_factory=list)


class AgentState(BaseModel):
    """LangGraph agent state."""
    release_branch: str
    version: str
    base_tag: Optional[str] = None
    dry_run: bool = False
    
    # Processing state
    current_step: str = "validate_release"
    error: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    
    # Data gathering
    context: Optional[ReleaseContext] = None
    
    # Results
    pr_url: Optional[str] = None
    pr_number: Optional[int] = None
    generated_files: List[str] = Field(default_factory=list)
    
    # Metadata
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

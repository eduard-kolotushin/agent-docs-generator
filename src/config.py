"""Configuration management for the release docs agent."""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Jira Configuration
    jira_base_url: str = Field(..., env="JIRA_BASE_URL")
    jira_email: str = Field(..., env="JIRA_EMAIL")
    jira_api_token: str = Field(..., env="JIRA_API_TOKEN")
    
    # Confluence Configuration
    confluence_base_url: str = Field(..., env="CONFLUENCE_BASE_URL")
    confluence_email: str = Field(..., env="CONFLUENCE_EMAIL")
    confluence_api_token: str = Field(..., env="CONFLUENCE_API_TOKEN")
    
    # Bitbucket Configuration
    bitbucket_workspace: str = Field(..., env="BITBUCKET_WORKSPACE")
    bitbucket_repo_slug: str = Field(..., env="BITBUCKET_REPO_SLUG")
    bitbucket_username: str = Field(..., env="BITBUCKET_USERNAME")
    bitbucket_app_password: str = Field(..., env="BITBUCKET_APP_PASSWORD")
    
    # Docs Repository (if different from main repo)
    docs_workspace: Optional[str] = Field(None, env="DOCS_WORKSPACE")
    docs_repo_slug: Optional[str] = Field(None, env="DOCS_REPO_SLUG")
    
    # LLM Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    
    # Optional Configuration
    dry_run: bool = Field(False, env="DRY_RUN")
    base_tag: Optional[str] = Field(None, env="BASE_TAG")
    release_labels: str = Field("breaking,docs", env="RELEASE_LABELS")
    pr_assignees: str = Field("team-docs", env="PR_ASSIGNEES")
    
    @property
    def docs_workspace_final(self) -> str:
        """Get the docs workspace, falling back to main workspace if not set."""
        return self.docs_workspace or self.bitbucket_workspace
    
    @property
    def docs_repo_slug_final(self) -> str:
        """Get the docs repo slug, falling back to main repo if not set."""
        return self.docs_repo_slug or self.bitbucket_repo_slug
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

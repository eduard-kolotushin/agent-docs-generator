"""Configuration management for the release docs agent."""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Jira Configuration
    jira_base_url: str = Field(default="https://example.atlassian.net", description="Jira base URL")
    jira_email: str = Field(default="user@example.com", description="Jira email")
    jira_api_token: str = Field(default="", description="Jira API token")
    
    # Confluence Configuration
    confluence_base_url: str = Field(default="https://example.atlassian.net", description="Confluence base URL")
    confluence_email: str = Field(default="user@example.com", description="Confluence email")
    confluence_api_token: str = Field(default="", description="Confluence API token")
    
    # Bitbucket Configuration
    bitbucket_workspace: str = Field(default="workspace", description="Bitbucket workspace")
    bitbucket_repo_slug: str = Field(default="repo", description="Bitbucket repository slug")
    bitbucket_username: str = Field(default="username", description="Bitbucket username")
    bitbucket_app_password: str = Field(default="", description="Bitbucket app password")
    
    # Docs Repository (if different from main repo)
    docs_workspace: Optional[str] = Field(default=None, description="Docs workspace")
    docs_repo_slug: Optional[str] = Field(default=None, description="Docs repository slug")
    
    # LLM Configuration
    openai_api_key: str = Field(default="", description="OpenAI API key")
    
    # Optional Configuration
    dry_run: bool = Field(default=False, description="Run in dry-run mode")
    base_tag: Optional[str] = Field(default=None, description="Base tag for comparison")
    release_labels: str = Field(default="breaking,docs", description="PR labels")
    pr_assignees: str = Field(default="team-docs", description="PR assignees")
    
    @property
    def docs_workspace_final(self) -> str:
        """Get the docs workspace, falling back to main workspace if not set."""
        return self.docs_workspace or self.bitbucket_workspace
    
    @property
    def docs_repo_slug_final(self) -> str:
        """Get the docs repo slug, falling back to main repo if not set."""
        return self.docs_repo_slug or self.bitbucket_repo_slug


# Global settings instance - only create if environment variables are available
def get_settings() -> Settings:
    """Get settings instance, with fallback for testing."""
    try:
        return Settings()
    except Exception:
        # Return settings with defaults for testing
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
            openai_api_key="test-key"
        )

settings = get_settings()

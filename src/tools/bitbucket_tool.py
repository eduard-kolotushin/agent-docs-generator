"""Bitbucket tool for LangGraph."""

from typing import List, Optional
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from ..clients.bitbucket_client import BitbucketClient
from ..schemas import BitbucketPR, BitbucketCommit
from ..config import settings


class BitbucketToolInput(BaseModel):
    """Input for Bitbucket tool."""
    branch_name: str = Field(description="Branch name to analyze (e.g., release/1.2.3)")
    base_tag: Optional[str] = Field(description="Base tag to compare against", default=None)
    workspace: Optional[str] = Field(description="Workspace name", default=None)
    repo_slug: Optional[str] = Field(description="Repository slug", default=None)


class BitbucketTool(BaseTool):
    """Tool for fetching Bitbucket data."""
    
    name = "bitbucket_tool"
    description = "Fetch Bitbucket PRs and commits for a release branch"
    args_schema = BitbucketToolInput
    
    def __init__(self):
        super().__init__()
        self.client = BitbucketClient()
    
    def _run(
        self,
        branch_name: str,
        base_tag: Optional[str] = None,
        workspace: Optional[str] = None,
        repo_slug: Optional[str] = None,
    ) -> dict:
        """Run the Bitbucket tool synchronously."""
        import asyncio
        return asyncio.run(self._arun(branch_name, base_tag, workspace, repo_slug))
    
    async def _arun(
        self,
        branch_name: str,
        base_tag: Optional[str] = None,
        workspace: Optional[str] = None,
        repo_slug: Optional[str] = None,
    ) -> dict:
        """Run the Bitbucket tool asynchronously."""
        try:
            # Use provided workspace/repo or fall back to settings
            workspace = workspace or settings.bitbucket_workspace
            repo_slug = repo_slug or settings.bitbucket_repo_slug
            
            # Check if branch exists
            branch_exists = await self.client.branch_exists(workspace, repo_slug, branch_name)
            if not branch_exists:
                return {
                    "error": f"Branch {branch_name} does not exist",
                    "prs": [],
                    "commits": []
                }
            
            # Fetch PRs and commits in parallel
            prs_task = self.client.get_pull_requests_for_branch(workspace, repo_slug, branch_name)
            commits_task = self.client.get_commits_for_branch(workspace, repo_slug, branch_name, base_tag)
            
            prs, commits = await asyncio.gather(prs_task, commits_task)
            
            # Get changed files for PRs and commits
            for pr in prs:
                pr.changed_files = await self.client.get_pull_request_changes(workspace, repo_slug, pr.id)
            
            for commit in commits:
                commit.changed_files = await self.client.get_commit_changes(workspace, repo_slug, commit.hash)
            
            return {
                "prs": [pr.model_dump() for pr in prs],
                "commits": [commit.model_dump() for commit in commits],
                "branch_exists": True
            }
            
        except Exception as e:
            print(f"Error in Bitbucket tool: {e}")
            return {
                "error": str(e),
                "prs": [],
                "commits": []
            }
        finally:
            await self.client.close()

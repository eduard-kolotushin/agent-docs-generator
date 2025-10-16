"""Jira tool for LangGraph."""

from typing import List, Optional
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from ..clients.jira_client import JiraClient
from ..schemas import JiraIssue


class JiraToolInput(BaseModel):
    """Input for Jira tool."""
    version: str = Field(description="Version to search for (e.g., 1.2.3)")
    search_type: str = Field(
        description="Type of search: 'fix_version', 'branch', or 'pr'",
        default="fix_version"
    )
    branch_name: Optional[str] = Field(description="Branch name for branch search", default=None)
    pr_id: Optional[int] = Field(description="PR ID for PR search", default=None)


class JiraTool(BaseTool):
    """Tool for fetching Jira issues."""
    
    name: str = "jira_tool"
    description: str = "Fetch Jira issues by fix version, branch, or PR"
    args_schema: type = JiraToolInput
    
    def __init__(self):
        super().__init__()
        self.client = JiraClient()
    
    def _run(
        self,
        version: str,
        search_type: str = "fix_version",
        branch_name: Optional[str] = None,
        pr_id: Optional[int] = None,
    ) -> List[dict]:
        """Run the Jira tool synchronously."""
        import asyncio
        return asyncio.run(self._arun(version, search_type, branch_name, pr_id))
    
    async def _arun(
        self,
        version: str,
        search_type: str = "fix_version",
        branch_name: Optional[str] = None,
        pr_id: Optional[int] = None,
    ) -> List[dict]:
        """Run the Jira tool asynchronously."""
        try:
            if search_type == "fix_version":
                issues = await self.client.get_issues_by_fix_version(version)
            elif search_type == "branch" and branch_name:
                issues = await self.client.get_issues_by_branch(branch_name)
            elif search_type == "pr" and pr_id:
                issues = await self.client.get_issues_by_pr(pr_id)
            else:
                return []
            
            # Convert to dict format for LangGraph
            return [issue.model_dump() for issue in issues]
            
        except Exception as e:
            print(f"Error in Jira tool: {e}")
            return []
        finally:
            await self.client.close()

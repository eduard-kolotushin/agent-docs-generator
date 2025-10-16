"""Jira API client for fetching issue data."""

import asyncio
from datetime import datetime
from typing import List, Optional

import httpx
from atlassian import Jira

from ..config import settings
from ..schemas import JiraIssue


class JiraClient:
    """Jira API client with async support."""
    
    def __init__(self):
        self.jira = Jira(
            url=settings.jira_base_url,
            username=settings.jira_email,
            password=settings.jira_api_token,
        )
        self._client = httpx.AsyncClient(
            auth=(settings.jira_email, settings.jira_api_token),
            timeout=30.0,
        )
    
    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
    
    async def get_issues_by_fix_version(self, version: str) -> List[JiraIssue]:
        """Get issues by fix version."""
        jql = f'fixVersion = "{version}" ORDER BY priority DESC, updated DESC'
        return await self._search_issues(jql)
    
    async def get_issues_by_branch(self, branch_name: str) -> List[JiraIssue]:
        """Get issues linked to a specific branch."""
        jql = f'text ~ "{branch_name}" OR "Branch name" ~ "{branch_name}"'
        return await self._search_issues(jql)
    
    async def get_issues_by_pr(self, pr_id: int) -> List[JiraIssue]:
        """Get issues linked to a specific PR."""
        jql = f'"Pull Request" ~ "{pr_id}" OR text ~ "PR #{pr_id}"'
        return await self._search_issues(jql)
    
    async def _search_issues(self, jql: str) -> List[JiraIssue]:
        """Search for issues using JQL."""
        try:
            # Use the sync client for JQL search
            issues = self.jira.jql(jql, limit=1000)
            
            result = []
            for issue_data in issues.get("issues", []):
                issue = self._parse_issue(issue_data)
                if issue:
                    result.append(issue)
            
            return result
            
        except Exception as e:
            print(f"Error searching Jira issues: {e}")
            return []
    
    def _parse_issue(self, issue_data: dict) -> Optional[JiraIssue]:
        """Parse Jira issue data into JiraIssue model."""
        try:
            fields = issue_data.get("fields", {})
            
            # Extract basic fields
            key = issue_data.get("key", "")
            summary = fields.get("summary", "")
            issue_type = fields.get("issuetype", {}).get("name", "")
            status = fields.get("status", {}).get("name", "")
            priority = fields.get("priority", {}).get("name", "")
            
            # Extract components
            components = [
                comp.get("name", "") 
                for comp in fields.get("components", [])
            ]
            
            # Extract labels
            labels = fields.get("labels", [])
            
            # Extract fix version
            fix_versions = fields.get("fixVersions", [])
            fix_version = fix_versions[0].get("name") if fix_versions else None
            
            # Extract epic
            epic = fields.get("parent", {})
            epic_key = epic.get("key") if epic else None
            
            # Extract changelog from description or comments
            description = fields.get("description", "")
            changelog = self._extract_changelog(description)
            
            # Check for breaking change labels
            breaking_change = any(
                label.lower() in ["breaking", "breaking-change", "breaking_change"]
                for label in labels
            )
            
            # Extract assignee and reporter
            assignee = fields.get("assignee", {}).get("displayName") if fields.get("assignee") else None
            reporter = fields.get("reporter", {}).get("displayName") if fields.get("reporter") else None
            
            # Parse dates
            created = datetime.fromisoformat(
                fields.get("created", "").replace("Z", "+00:00")
            )
            updated = datetime.fromisoformat(
                fields.get("updated", "").replace("Z", "+00:00")
            )
            
            return JiraIssue(
                key=key,
                summary=summary,
                issue_type=issue_type,
                status=status,
                priority=priority,
                components=components,
                labels=labels,
                fix_version=fix_version,
                epic_key=epic_key,
                changelog=changelog,
                breaking_change=breaking_change,
                assignee=assignee,
                reporter=reporter,
                created=created,
                updated=updated,
            )
            
        except Exception as e:
            print(f"Error parsing Jira issue {issue_data.get('key', 'unknown')}: {e}")
            return None
    
    def _extract_changelog(self, description: str) -> Optional[str]:
        """Extract changelog information from issue description."""
        if not description:
            return None
        
        # Look for common changelog patterns
        lines = description.split('\n')
        changelog_lines = []
        in_changelog = False
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ["changelog", "what's new", "changes"]):
                in_changelog = True
                continue
            elif in_changelog and line and not line.startswith('#'):
                changelog_lines.append(line)
            elif in_changelog and line.startswith('#'):
                break
        
        return '\n'.join(changelog_lines) if changelog_lines else None

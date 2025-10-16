"""Bitbucket API client for fetching repository data."""

import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import quote

import httpx

from ..config import settings
from ..schemas import BitbucketPR, BitbucketCommit


class BitbucketClient:
    """Bitbucket API client with async support."""
    
    def __init__(self):
        self.base_url = f"https://api.bitbucket.org/2.0"
        self.auth = (settings.bitbucket_username, settings.bitbucket_app_password)
        self._client = httpx.AsyncClient(auth=self.auth, timeout=30.0)
    
    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
    
    async def get_pull_requests_for_branch(
        self, 
        workspace: str, 
        repo_slug: str, 
        branch_name: str
    ) -> List[BitbucketPR]:
        """Get pull requests targeting a specific branch."""
        url = f"{self.base_url}/repositories/{workspace}/{repo_slug}/pullrequests"
        params = {
            "q": f'destination.branch.name = "{branch_name}"',
            "pagelen": 100,
        }
        
        try:
            response = await self._client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            prs = []
            for pr_data in data.get("values", []):
                pr = self._parse_pull_request(pr_data)
                if pr:
                    prs.append(pr)
            
            return prs
            
        except Exception as e:
            print(f"Error fetching PRs for branch {branch_name}: {e}")
            return []
    
    async def get_commits_for_branch(
        self,
        workspace: str,
        repo_slug: str,
        branch_name: str,
        base_tag: Optional[str] = None
    ) -> List[BitbucketCommit]:
        """Get commits for a branch, optionally since a base tag."""
        url = f"{self.base_url}/repositories/{workspace}/{repo_slug}/commits/{branch_name}"
        params = {"pagelen": 100}
        
        if base_tag:
            params["exclude"] = f"refs/tags/{base_tag}"
        
        try:
            response = await self._client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            commits = []
            for commit_data in data.get("values", []):
                commit = self._parse_commit(commit_data)
                if commit:
                    commits.append(commit)
            
            return commits
            
        except Exception as e:
            print(f"Error fetching commits for branch {branch_name}: {e}")
            return []
    
    async def get_pull_request_changes(
        self,
        workspace: str,
        repo_slug: str,
        pr_id: int
    ) -> List[str]:
        """Get changed files for a pull request."""
        url = f"{self.base_url}/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}/diffstat"
        
        try:
            response = await self._client.get(url)
            response.raise_for_status()
            data = response.json()
            
            changed_files = []
            for file_data in data.get("values", []):
                file_path = file_data.get("new", {}).get("path")
                if file_path:
                    changed_files.append(file_path)
            
            return changed_files
            
        except Exception as e:
            print(f"Error fetching changes for PR {pr_id}: {e}")
            return []
    
    async def get_commit_changes(
        self,
        workspace: str,
        repo_slug: str,
        commit_hash: str
    ) -> List[str]:
        """Get changed files for a commit."""
        url = f"{self.base_url}/repositories/{workspace}/{repo_slug}/diffstat/{commit_hash}"
        
        try:
            response = await self._client.get(url)
            response.raise_for_status()
            data = response.json()
            
            changed_files = []
            for file_data in data.get("values", []):
                file_path = file_data.get("new", {}).get("path")
                if file_path:
                    changed_files.append(file_path)
            
            return changed_files
            
        except Exception as e:
            print(f"Error fetching changes for commit {commit_hash}: {e}")
            return []
    
    async def branch_exists(
        self,
        workspace: str,
        repo_slug: str,
        branch_name: str
    ) -> bool:
        """Check if a branch exists."""
        url = f"{self.base_url}/repositories/{workspace}/{repo_slug}/refs/branches/{quote(branch_name)}"
        
        try:
            response = await self._client.get(url)
            return response.status_code == 200
        except Exception:
            return False
    
    def _parse_pull_request(self, pr_data: dict) -> Optional[BitbucketPR]:
        """Parse Bitbucket PR data into BitbucketPR model."""
        try:
            # Extract basic fields
            pr_id = pr_data.get("id", 0)
            title = pr_data.get("title", "")
            description = pr_data.get("description", "")
            
            # Extract author
            author_data = pr_data.get("author", {})
            author = author_data.get("display_name", author_data.get("username", ""))
            
            # Extract branches
            source = pr_data.get("source", {})
            destination = pr_data.get("destination", {})
            source_branch = source.get("branch", {}).get("name", "")
            target_branch = destination.get("branch", {}).get("name", "")
            
            # Extract state
            state = pr_data.get("state", "")
            
            # Parse dates
            created_on = datetime.fromisoformat(
                pr_data.get("created_on", "").replace("Z", "+00:00")
            )
            updated_on = datetime.fromisoformat(
                pr_data.get("updated_on", "").replace("Z", "+00:00")
            )
            
            # Extract links
            links = pr_data.get("links", {})
            
            # Extract linked issues from description
            linked_issues = self._extract_linked_issues(description)
            
            return BitbucketPR(
                id=pr_id,
                title=title,
                description=description,
                author=author,
                source_branch=source_branch,
                target_branch=target_branch,
                state=state,
                created_on=created_on,
                updated_on=updated_on,
                links=links,
                linked_issues=linked_issues,
                changed_files=[],  # Will be populated separately
            )
            
        except Exception as e:
            print(f"Error parsing PR {pr_data.get('id', 'unknown')}: {e}")
            return None
    
    def _parse_commit(self, commit_data: dict) -> Optional[BitbucketCommit]:
        """Parse Bitbucket commit data into BitbucketCommit model."""
        try:
            # Extract basic fields
            commit_hash = commit_data.get("hash", "")
            message = commit_data.get("message", "")
            
            # Extract author
            author_data = commit_data.get("author", {})
            author = author_data.get("user", {}).get("display_name", author_data.get("raw", ""))
            
            # Parse date
            date = datetime.fromisoformat(
                commit_data.get("date", "").replace("Z", "+00:00")
            )
            
            # Extract links
            links = commit_data.get("links", {})
            
            return BitbucketCommit(
                hash=commit_hash,
                message=message,
                author=author,
                date=date,
                links=links,
                changed_files=[],  # Will be populated separately
            )
            
        except Exception as e:
            print(f"Error parsing commit {commit_data.get('hash', 'unknown')}: {e}")
            return None
    
    def _extract_linked_issues(self, description: str) -> List[str]:
        """Extract linked issue keys from PR description."""
        if not description:
            return []
        
        import re
        # Look for Jira issue keys (e.g., PROJ-123, ABC-456)
        pattern = r'\b[A-Z][A-Z0-9]+-\d+\b'
        return re.findall(pattern, description)

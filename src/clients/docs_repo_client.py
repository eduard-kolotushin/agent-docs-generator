"""Client for managing documentation repository operations."""

import os
import tempfile
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path

import httpx
from git import Repo, GitCommandError

from ..config import settings
from ..schemas import DocEdit


class DocsRepoClient:
    """Client for managing documentation repository operations."""
    
    def __init__(self):
        self.workspace = settings.docs_workspace_final
        self.repo_slug = settings.docs_repo_slug_final
        self.auth = (settings.bitbucket_username, settings.bitbucket_app_password)
        self.base_url = "https://api.bitbucket.org/2.0"
        self._client = httpx.AsyncClient(auth=self.auth, timeout=30.0)
        self._temp_dir = None
        self._repo = None
    
    async def close(self):
        """Close the HTTP client and clean up."""
        await self._client.aclose()
        if self._temp_dir and os.path.exists(self._temp_dir):
            import shutil
            shutil.rmtree(self._temp_dir, ignore_errors=True)
    
    async def clone_repo(self) -> str:
        """Clone the documentation repository to a temporary directory."""
        try:
            # Create temporary directory
            self._temp_dir = tempfile.mkdtemp(prefix="docs_repo_")
            
            # Clone the repository
            repo_url = f"https://{settings.bitbucket_username}:{settings.bitbucket_app_password}@bitbucket.org/{self.workspace}/{self.repo_slug}.git"
            
            self._repo = Repo.clone_from(repo_url, self._temp_dir)
            
            return self._temp_dir
            
        except GitCommandError as e:
            raise Exception(f"Failed to clone repository: {e}")
    
    async def create_branch(self, branch_name: str) -> bool:
        """Create a new branch for the documentation changes."""
        try:
            if not self._repo:
                await self.clone_repo()
            
            # Check if branch already exists
            if branch_name in [ref.name for ref in self._repo.refs]:
                # Switch to existing branch
                self._repo.git.checkout(branch_name)
                return True
            
            # Create new branch
            self._repo.git.checkout("-b", branch_name)
            return True
            
        except GitCommandError as e:
            raise Exception(f"Failed to create branch {branch_name}: {e}")
    
    async def apply_edits(self, doc_edits: List[DocEdit]) -> List[str]:
        """Apply the document edits to the repository."""
        if not self._repo:
            await self.clone_repo()
        
        created_files = []
        
        for edit in doc_edits:
            file_path = os.path.join(self._temp_dir, edit.file_path)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            if edit.operation == "create":
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(edit.content or "")
                created_files.append(edit.file_path)
                
            elif edit.operation == "update":
                if os.path.exists(file_path):
                    # Read existing content
                    with open(file_path, "r", encoding="utf-8") as f:
                        existing_content = f.read()
                    
                    # Apply update (simple append for now)
                    updated_content = existing_content + "\n\n" + (edit.content or "")
                    
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(updated_content)
                else:
                    # Create new file
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(edit.content or "")
                
                created_files.append(edit.file_path)
                
            elif edit.operation == "delete":
                if os.path.exists(file_path):
                    os.remove(file_path)
        
        return created_files
    
    async def commit_changes(self, message: str) -> str:
        """Commit the changes to the repository."""
        try:
            if not self._repo:
                raise Exception("Repository not initialized")
            
            # Add all changes
            self._repo.git.add(".")
            
            # Check if there are changes to commit
            if not self._repo.is_dirty() and not self._repo.untracked_files:
                return "No changes to commit"
            
            # Commit changes
            commit = self._repo.index.commit(message)
            return commit.hexsha
            
        except GitCommandError as e:
            raise Exception(f"Failed to commit changes: {e}")
    
    async def push_branch(self, branch_name: str) -> bool:
        """Push the branch to the remote repository."""
        try:
            if not self._repo:
                raise Exception("Repository not initialized")
            
            # Push the branch
            self._repo.git.push("origin", branch_name)
            return True
            
        except GitCommandError as e:
            raise Exception(f"Failed to push branch {branch_name}: {e}")
    
    async def create_pull_request(
        self,
        branch_name: str,
        title: str,
        description: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a pull request for the documentation changes."""
        try:
            url = f"{self.base_url}/repositories/{self.workspace}/{self.repo_slug}/pullrequests"
            
            # Get the main branch (usually 'main' or 'master')
            main_branch = await self._get_main_branch()
            
            pr_data = {
                "title": title,
                "description": description,
                "source": {
                    "branch": {
                        "name": branch_name
                    }
                },
                "destination": {
                    "branch": {
                        "name": main_branch
                    }
                }
            }
            
            response = await self._client.post(url, json=pr_data)
            response.raise_for_status()
            
            pr_info = response.json()
            
            # Add labels if provided
            if labels:
                await self._add_pr_labels(pr_info["id"], labels)
            
            # Add assignees if provided
            if assignees:
                await self._add_pr_assignees(pr_info["id"], assignees)
            
            return {
                "pr_url": pr_info["links"]["html"]["href"],
                "pr_number": pr_info["id"],
                "pr_id": pr_info["id"]
            }
            
        except Exception as e:
            raise Exception(f"Failed to create pull request: {e}")
    
    async def _get_main_branch(self) -> str:
        """Get the main branch name for the repository."""
        try:
            url = f"{self.base_url}/repositories/{self.workspace}/{self.repo_slug}"
            response = await self._client.get(url)
            response.raise_for_status()
            
            repo_info = response.json()
            return repo_info.get("mainbranch", {}).get("name", "main")
            
        except Exception:
            return "main"  # Default fallback
    
    async def _add_pr_labels(self, pr_id: int, labels: List[str]) -> bool:
        """Add labels to a pull request."""
        try:
            # Note: Bitbucket doesn't have native label support in the API
            # This would need to be implemented differently or skipped
            return True
            
        except Exception as e:
            print(f"Warning: Failed to add labels to PR {pr_id}: {e}")
            return False
    
    async def _add_pr_assignees(self, pr_id: int, assignees: List[str]) -> bool:
        """Add assignees to a pull request."""
        try:
            # Note: Bitbucket PR assignees are not easily set via API
            # This would need to be implemented differently or skipped
            return True
            
        except Exception as e:
            print(f"Warning: Failed to add assignees to PR {pr_id}: {e}")
            return False

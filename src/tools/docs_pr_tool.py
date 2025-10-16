"""Docs PR tool for LangGraph."""

import os
import tempfile
from typing import List, Dict, Any, Optional
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from ..config import settings
from ..schemas import DocEdit
from ..clients.docs_repo_client import DocsRepoClient


class DocsPRToolInput(BaseModel):
    """Input for Docs PR tool."""
    doc_edits: List[Dict[str, Any]] = Field(description="List of document edits to apply")
    version: str = Field(description="Release version (e.g., 1.2.3)")
    pr_title: Optional[str] = Field(description="PR title", default=None)
    pr_description: Optional[str] = Field(description="PR description", default=None)
    labels: Optional[List[str]] = Field(description="PR labels", default=None)
    assignees: Optional[List[str]] = Field(description="PR assignees", default=None)


class DocsPRTool(BaseTool):
    """Tool for creating documentation PRs."""
    
    name = "docs_pr_tool"
    description = "Create a PR with documentation updates"
    args_schema = DocsPRToolInput
    
    def __init__(self):
        super().__init__()
        self.workspace = settings.docs_workspace_final
        self.repo_slug = settings.docs_repo_slug_final
        self.dry_run = settings.dry_run
    
    def _run(
        self,
        doc_edits: List[Dict[str, Any]],
        version: str,
        pr_title: Optional[str] = None,
        pr_description: Optional[str] = None,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
    ) -> dict:
        """Run the Docs PR tool synchronously."""
        import asyncio
        return asyncio.run(self._arun(doc_edits, version, pr_title, pr_description, labels, assignees))
    
    async def _arun(
        self,
        doc_edits: List[Dict[str, Any]],
        version: str,
        pr_title: Optional[str] = None,
        pr_description: Optional[str] = None,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
    ) -> dict:
        """Run the Docs PR tool asynchronously."""
        try:
            if self.dry_run:
                return await self._create_dry_run_files(doc_edits, version)
            else:
                return await self._create_pr(doc_edits, version, pr_title, pr_description, labels, assignees)
                
        except Exception as e:
            print(f"Error in Docs PR tool: {e}")
            return {"error": str(e)}
    
    async def _create_dry_run_files(
        self, 
        doc_edits: List[Dict[str, Any]], 
        version: str
    ) -> dict:
        """Create files in dry-run mode."""
        output_dir = "./out"
        os.makedirs(output_dir, exist_ok=True)
        
        created_files = []
        
        for edit_data in doc_edits:
            file_path = edit_data.get("file_path", "")
            operation = edit_data.get("operation", "")
            content = edit_data.get("content", "")
            
            if operation in ["create", "update"] and content:
                full_path = os.path.join(output_dir, file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)
                
                created_files.append(file_path)
        
        return {
            "dry_run": True,
            "created_files": created_files,
            "output_dir": output_dir
        }
    
    async def _create_pr(
        self,
        doc_edits: List[Dict[str, Any]],
        version: str,
        pr_title: Optional[str] = None,
        pr_description: Optional[str] = None,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
    ) -> dict:
        """Create a PR with the documentation changes."""
        try:
            client = DocsRepoClient()
            
            # Clone the repository
            await client.clone_repo()
            
            # Create branch
            branch_name = f"docs/release-{version}"
            await client.create_branch(branch_name)
            
            # Convert dict edits to DocEdit objects
            doc_edit_objects = [DocEdit(**edit) for edit in doc_edits]
            
            # Apply edits
            created_files = await client.apply_edits(doc_edit_objects)
            
            # Commit changes
            commit_message = f"docs: Update documentation for release {version}"
            commit_hash = await client.commit_changes(commit_message)
            
            # Push branch
            await client.push_branch(branch_name)
            
            # Create PR
            pr_result = await client.create_pull_request(
                branch_name=branch_name,
                title=pr_title or f"Docs: Release {version}",
                description=pr_description or f"Automated documentation updates for release {version}",
                labels=labels,
                assignees=assignees
            )
            
            await client.close()
            
            return {
                "pr_url": pr_result["pr_url"],
                "pr_number": pr_result["pr_number"],
                "branch_name": branch_name,
                "commit_hash": commit_hash,
                "created_files": created_files
            }
            
        except Exception as e:
            return {
                "error": f"Failed to create PR: {e}",
                "created_files": []
            }

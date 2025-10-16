"""Confluence tool for LangGraph."""

from typing import List, Optional
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from ..clients.confluence_client import ConfluenceClient
from ..schemas import ConfluencePage


class ConfluenceToolInput(BaseModel):
    """Input for Confluence tool."""
    search_type: str = Field(
        description="Type of search: 'release_notes', 'labels', or 'search'",
        default="release_notes"
    )
    query: Optional[str] = Field(description="Search query for search type", default=None)
    labels: Optional[List[str]] = Field(description="Labels to search for", default=None)
    space_key: str = Field(description="Confluence space key", default="DOCS")


class ConfluenceTool(BaseTool):
    """Tool for fetching Confluence pages."""
    
    name: str = "confluence_tool"
    description: str = "Fetch Confluence pages for context and reference"
    args_schema: type = ConfluenceToolInput
    
    def __init__(self):
        super().__init__()
        self.client = ConfluenceClient()
    
    def _run(
        self,
        search_type: str = "release_notes",
        query: Optional[str] = None,
        labels: Optional[List[str]] = None,
        space_key: str = "DOCS",
    ) -> List[dict]:
        """Run the Confluence tool synchronously."""
        import asyncio
        return asyncio.run(self._arun(search_type, query, labels, space_key))
    
    async def _arun(
        self,
        search_type: str = "release_notes",
        query: Optional[str] = None,
        labels: Optional[List[str]] = None,
        space_key: str = "DOCS",
    ) -> List[dict]:
        """Run the Confluence tool asynchronously."""
        try:
            pages = []
            
            if search_type == "release_notes":
                page = await self.client.get_release_notes_page(space_key)
                if page:
                    pages = [page]
            elif search_type == "labels" and labels:
                pages = await self.client.get_pages_by_labels(labels, space_key)
            elif search_type == "search" and query:
                pages = await self.client.search_pages(query, space_key)
            
            # Convert to dict format for LangGraph
            return [page.model_dump() for page in pages]
            
        except Exception as e:
            print(f"Error in Confluence tool: {e}")
            return []
        finally:
            await self.client.close()

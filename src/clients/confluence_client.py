"""Confluence API client for fetching page data."""

import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any

import httpx
from atlassian import Confluence

from ..config import settings
from ..schemas import ConfluencePage


class ConfluenceClient:
    """Confluence API client with async support."""
    
    def __init__(self):
        self.confluence = Confluence(
            url=settings.confluence_base_url,
            username=settings.confluence_email,
            password=settings.confluence_api_token,
        )
        self._client = httpx.AsyncClient(
            auth=(settings.confluence_email, settings.confluence_api_token),
            timeout=30.0,
        )
    
    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
    
    async def get_release_notes_page(self, space_key: str = "DOCS") -> Optional[ConfluencePage]:
        """Get the latest release notes page."""
        try:
            # Search for release notes pages
            pages = self.confluence.get_all_pages_from_space(
                space=space_key,
                start=0,
                limit=50,
                content_type="page",
                expand="body.storage,version,space,ancestors"
            )
            
            # Find the most recent release notes page
            release_notes_pages = [
                page for page in pages
                if any(keyword in page.get("title", "").lower() 
                      for keyword in ["release notes", "release notes", "changelog"])
            ]
            
            if not release_notes_pages:
                return None
            
            # Sort by creation date and get the most recent
            latest_page = max(
                release_notes_pages,
                key=lambda p: p.get("version", {}).get("when", "")
            )
            
            return self._parse_page(latest_page)
            
        except Exception as e:
            print(f"Error fetching release notes page: {e}")
            return None
    
    async def get_pages_by_labels(
        self, 
        labels: List[str], 
        space_key: str = "DOCS"
    ) -> List[ConfluencePage]:
        """Get pages by labels."""
        try:
            pages = []
            for label in labels:
                # Search for pages with specific label
                search_results = self.confluence.cql(
                    f'label = "{label}" AND space = "{space_key}"',
                    limit=50
                )
                
                for result in search_results.get("results", []):
                    page_id = result.get("content", {}).get("id")
                    if page_id:
                        page = self.confluence.get_page_by_id(
                            page_id,
                            expand="body.storage,version,space,ancestors,metadata.labels"
                        )
                        if page:
                            parsed_page = self._parse_page(page)
                            if parsed_page:
                                pages.append(parsed_page)
            
            return pages
            
        except Exception as e:
            print(f"Error fetching pages by labels: {e}")
            return []
    
    async def search_pages(
        self, 
        query: str, 
        space_key: str = "DOCS",
        limit: int = 20
    ) -> List[ConfluencePage]:
        """Search for pages by query."""
        try:
            # Use CQL to search for pages
            search_results = self.confluence.cql(
                f'text ~ "{query}" AND space = "{space_key}"',
                limit=limit
            )
            
            pages = []
            for result in search_results.get("results", []):
                page_id = result.get("content", {}).get("id")
                if page_id:
                    page = self.confluence.get_page_by_id(
                        page_id,
                        expand="body.storage,version,space,ancestors,metadata.labels"
                    )
                    if page:
                        parsed_page = self._parse_page(page)
                        if parsed_page:
                            pages.append(parsed_page)
            
            return pages
            
        except Exception as e:
            print(f"Error searching pages: {e}")
            return []
    
    async def get_page_attachments(self, page_id: str) -> List[Dict[str, Any]]:
        """Get attachments for a page."""
        try:
            attachments = self.confluence.get_attachments_from_content(
                page_id,
                start=0,
                limit=100
            )
            
            return [
                {
                    "id": att.get("id"),
                    "title": att.get("title"),
                    "file_size": att.get("extensions", {}).get("fileSize"),
                    "media_type": att.get("extensions", {}).get("mediaType"),
                    "download_url": att.get("_links", {}).get("download"),
                }
                for att in attachments.get("results", [])
            ]
            
        except Exception as e:
            print(f"Error fetching attachments for page {page_id}: {e}")
            return []
    
    async def download_attachment(
        self, 
        page_id: str, 
        attachment_id: str,
        filename: str
    ) -> Optional[bytes]:
        """Download an attachment."""
        try:
            # Get the download URL
            attachment = self.confluence.get_attachment_by_id(attachment_id)
            download_url = attachment.get("_links", {}).get("download")
            
            if not download_url:
                return None
            
            # Download the file
            response = await self._client.get(download_url)
            response.raise_for_status()
            
            return response.content
            
        except Exception as e:
            print(f"Error downloading attachment {attachment_id}: {e}")
            return None
    
    def _parse_page(self, page_data: dict) -> Optional[ConfluencePage]:
        """Parse Confluence page data into ConfluencePage model."""
        try:
            # Extract basic fields
            page_id = page_data.get("id", "")
            title = page_data.get("title", "")
            space_key = page_data.get("space", {}).get("key", "")
            
            # Extract content
            body = page_data.get("body", {}).get("storage", {}).get("value", "")
            
            # Extract version
            version = page_data.get("version", {}).get("number", 1)
            
            # Parse dates
            created = datetime.fromisoformat(
                page_data.get("version", {}).get("when", "").replace("Z", "+00:00")
            )
            updated = datetime.fromisoformat(
                page_data.get("version", {}).get("when", "").replace("Z", "+00:00")
            )
            
            # Extract labels
            labels = []
            metadata = page_data.get("metadata", {})
            if metadata:
                labels_data = metadata.get("labels", {}).get("results", [])
                labels = [label.get("name", "") for label in labels_data]
            
            # Get attachments
            attachments = page_data.get("_links", {}).get("attachments", [])
            
            return ConfluencePage(
                id=page_id,
                title=title,
                content=body,
                space_key=space_key,
                version=version,
                created=created,
                updated=updated,
                labels=labels,
                attachments=attachments,
            )
            
        except Exception as e:
            print(f"Error parsing page {page_data.get('id', 'unknown')}: {e}")
            return None

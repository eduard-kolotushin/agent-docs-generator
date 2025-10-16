"""Generator for creating release notes."""

from typing import List
from langchain_openai import ChatOpenAI
from jinja2 import Template

from ..schemas import ReleaseContext
from ..config import settings
from ..prompts.release_notes_prompt import RELEASE_NOTES_PROMPT


async def generate_release_notes(context: ReleaseContext) -> str:
    """Generate release notes for the given context."""
    
    # Initialize LLM
    llm = ChatOpenAI(
        model="gpt-4",
        temperature=0.1,
        api_key=settings.openai_api_key
    )
    
    # Format Jira issues
    jira_issues_text = format_jira_issues(context.jira_issues)
    
    # Format Bitbucket PRs
    bitbucket_prs_text = format_bitbucket_prs(context.bitbucket_prs)
    
    # Format Bitbucket commits
    bitbucket_commits_text = format_bitbucket_commits(context.bitbucket_commits)
    
    # Get previous release notes for reference
    previous_release_notes = get_previous_release_notes(context.confluence_pages)
    
    # Create the prompt
    prompt = RELEASE_NOTES_PROMPT.format(
        version=context.version,
        release_branch=context.release_branch,
        base_tag=context.base_tag or "auto-detect",
        jira_issues=jira_issues_text,
        bitbucket_prs=bitbucket_prs_text,
        bitbucket_commits=bitbucket_commits_text,
        previous_release_notes=previous_release_notes
    )
    
    # Generate release notes
    response = await llm.ainvoke(prompt)
    
    return response.content


def format_jira_issues(issues: List) -> str:
    """Format Jira issues for the prompt."""
    if not issues:
        return "No Jira issues found."
    
    formatted_issues = []
    for issue in issues:
        formatted_issues.append(f"""
- **{issue.key}**: {issue.summary}
  - Type: {issue.issue_type}
  - Status: {issue.status}
  - Priority: {issue.priority}
  - Components: {', '.join(issue.components)}
  - Labels: {', '.join(issue.labels)}
  - Breaking Change: {issue.breaking_change}
  - Changelog: {issue.changelog or 'N/A'}
""")
    
    return "\n".join(formatted_issues)


def format_bitbucket_prs(prs: List) -> str:
    """Format Bitbucket PRs for the prompt."""
    if not prs:
        return "No pull requests found."
    
    formatted_prs = []
    for pr in prs:
        formatted_prs.append(f"""
- **PR #{pr.id}**: {pr.title}
  - Author: {pr.author}
  - State: {pr.state}
  - Source: {pr.source_branch} → {pr.target_branch}
  - Description: {pr.description or 'N/A'}
  - Linked Issues: {', '.join(pr.linked_issues)}
  - Changed Files: {len(pr.changed_files)} files
""")
    
    return "\n".join(formatted_prs)


def format_bitbucket_commits(commits: List) -> str:
    """Format Bitbucket commits for the prompt."""
    if not commits:
        return "No commits found."
    
    formatted_commits = []
    for commit in commits:
        formatted_commits.append(f"""
- **{commit.hash[:8]}**: {commit.message}
  - Author: {commit.author}
  - Date: {commit.date}
  - Changed Files: {len(commit.changed_files)} files
""")
    
    return "\n".join(formatted_commits)


def get_previous_release_notes(pages: List) -> str:
    """Extract previous release notes from Confluence pages."""
    for page in pages:
        if any(keyword in page.title.lower() for keyword in ["release notes", "changelog"]):
            return page.content[:2000] + "..." if len(page.content) > 2000 else page.content
    
    return "No previous release notes found."

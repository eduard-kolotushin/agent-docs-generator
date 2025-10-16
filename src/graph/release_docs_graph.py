"""LangGraph definition for the release docs agent."""

from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from ..schemas import AgentState, ReleaseContext, JiraIssue, BitbucketPR, BitbucketCommit, ConfluencePage, DocEdit
from ..tools.jira_tool import JiraTool
from ..tools.bitbucket_tool import BitbucketTool
from ..tools.confluence_tool import ConfluenceTool
from ..tools.docs_pr_tool import DocsPRTool
from ..config import settings


def create_release_docs_graph() -> StateGraph:
    """Create the release docs agent graph."""
    
    # Initialize tools
    jira_tool = JiraTool()
    bitbucket_tool = BitbucketTool()
    confluence_tool = ConfluenceTool()
    docs_pr_tool = DocsPRTool()
    
    # Initialize LLM
    llm = ChatOpenAI(
        model="gpt-4",
        temperature=0.1,
        api_key=settings.openai_api_key
    )
    
    # Create the graph
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("validate_release", validate_release)
    graph.add_node("gather_jira", gather_jira_data)
    graph.add_node("gather_bitbucket", gather_bitbucket_data)
    graph.add_node("gather_confluence", gather_confluence_data)
    graph.add_node("aggregate_context", aggregate_context)
    graph.add_node("generate_release_docs", generate_release_docs)
    graph.add_node("plan_file_edits", plan_file_edits)
    graph.add_node("create_docs_branch", create_docs_branch)
    graph.add_node("apply_file_edits", apply_file_edits)
    graph.add_node("open_pr", open_pr)
    graph.add_node("reviewer_reflection", reviewer_reflection)
    
    # Define the flow
    graph.set_entry_point("validate_release")
    
    # After validation, gather data in parallel
    graph.add_edge("validate_release", "gather_jira")
    graph.add_edge("validate_release", "gather_bitbucket")
    graph.add_edge("validate_release", "gather_confluence")
    
    # After gathering, aggregate context
    graph.add_edge("gather_jira", "aggregate_context")
    graph.add_edge("gather_bitbucket", "aggregate_context")
    graph.add_edge("gather_confluence", "aggregate_context")
    
    # Generate documentation
    graph.add_edge("aggregate_context", "generate_release_docs")
    graph.add_edge("generate_release_docs", "plan_file_edits")
    graph.add_edge("plan_file_edits", "create_docs_branch")
    graph.add_edge("create_docs_branch", "apply_file_edits")
    graph.add_edge("apply_file_edits", "open_pr")
    graph.add_edge("open_pr", "reviewer_reflection")
    graph.add_edge("reviewer_reflection", END)
    
    return graph.compile()


async def validate_release(state: AgentState) -> Dict[str, Any]:
    """Validate the release branch and extract version."""
    try:
        # Extract version from release branch
        version = state.version
        
        # Basic validation
        if not version or not version.replace(".", "").replace("-", "").isdigit():
            return {
                "error": f"Invalid version format: {version}",
                "current_step": "validate_release"
            }
        
        return {
            "current_step": "gather_data",
            "warnings": []
        }
        
    except Exception as e:
        return {
            "error": f"Error validating release: {e}",
            "current_step": "validate_release"
        }


async def gather_jira_data(state: AgentState) -> Dict[str, Any]:
    """Gather Jira issues for the release."""
    try:
        jira_tool = JiraTool()
        
        # Try fix version first
        issues_data = await jira_tool._arun(
            version=state.version,
            search_type="fix_version"
        )
        
        # If no issues found, try branch search
        if not issues_data:
            issues_data = await jira_tool._arun(
                version=state.version,
                search_type="branch",
                branch_name=state.release_branch
            )
        
        # Parse issues
        issues = [JiraIssue(**issue_data) for issue_data in issues_data]
        
        return {
            "context": ReleaseContext(
                version=state.version,
                release_branch=state.release_branch,
                base_tag=state.base_tag,
                jira_issues=issues
            )
        }
        
    except Exception as e:
        return {
            "error": f"Error gathering Jira data: {e}",
            "warnings": [f"Failed to gather Jira data: {e}"]
        }


async def gather_bitbucket_data(state: AgentState) -> Dict[str, Any]:
    """Gather Bitbucket PRs and commits for the release."""
    try:
        bitbucket_tool = BitbucketTool()
        
        result = await bitbucket_tool._arun(
            branch_name=state.release_branch,
            base_tag=state.base_tag
        )
        
        if result.get("error"):
            return {
                "error": result["error"],
                "warnings": [f"Bitbucket error: {result['error']}"]
            }
        
        # Parse PRs and commits
        prs = [BitbucketPR(**pr_data) for pr_data in result.get("prs", [])]
        commits = [BitbucketCommit(**commit_data) for commit_data in result.get("commits", [])]
        
        return {
            "context": ReleaseContext(
                version=state.version,
                release_branch=state.release_branch,
                base_tag=state.base_tag,
                bitbucket_prs=prs,
                bitbucket_commits=commits
            )
        }
        
    except Exception as e:
        return {
            "error": f"Error gathering Bitbucket data: {e}",
            "warnings": [f"Failed to gather Bitbucket data: {e}"]
        }


async def gather_confluence_data(state: AgentState) -> Dict[str, Any]:
    """Gather Confluence pages for context."""
    try:
        confluence_tool = ConfluenceTool()
        
        # Get release notes page
        release_notes_data = await confluence_tool._arun(
            search_type="release_notes"
        )
        
        # Get pages by labels from Jira issues
        labels = []
        if state.context and state.context.jira_issues:
            for issue in state.context.jira_issues:
                labels.extend(issue.labels)
        
        pages_data = []
        if labels:
            pages_data = await confluence_tool._arun(
                search_type="labels",
                labels=list(set(labels))
            )
        
        # Parse pages
        pages = [ConfluencePage(**page_data) for page_data in release_notes_data + pages_data]
        
        return {
            "context": ReleaseContext(
                version=state.version,
                release_branch=state.release_branch,
                base_tag=state.base_tag,
                confluence_pages=pages
            )
        }
        
    except Exception as e:
        return {
            "error": f"Error gathering Confluence data: {e}",
            "warnings": [f"Failed to gather Confluence data: {e}"]
        }


async def aggregate_context(state: AgentState) -> Dict[str, Any]:
    """Aggregate all gathered context and analyze it."""
    try:
        # Merge contexts from different sources
        context = ReleaseContext(
            version=state.version,
            release_branch=state.release_branch,
            base_tag=state.base_tag
        )
        
        # Add Jira issues
        if state.context and state.context.jira_issues:
            context.jira_issues = state.context.jira_issues
        
        # Add Bitbucket data
        if state.context and state.context.bitbucket_prs:
            context.bitbucket_prs = state.context.bitbucket_prs
        if state.context and state.context.bitbucket_commits:
            context.bitbucket_commits = state.context.bitbucket_commits
        
        # Add Confluence pages
        if state.context and state.context.confluence_pages:
            context.confluence_pages = state.context.confluence_pages
        
        # Analyze the data
        context = analyze_release_context(context)
        
        return {
            "context": context,
            "current_step": "generate_docs"
        }
        
    except Exception as e:
        return {
            "error": f"Error aggregating context: {e}",
            "current_step": "aggregate_context"
        }


def analyze_release_context(context: ReleaseContext) -> ReleaseContext:
    """Analyze the release context and categorize issues."""
    
    # Categorize Jira issues
    for issue in context.jira_issues:
        if issue.breaking_change:
            context.breaking_changes.append(issue)
        elif issue.issue_type.lower() in ["story", "feature", "epic"]:
            context.new_features.append(issue)
        elif issue.issue_type.lower() in ["bug", "defect"]:
            context.bug_fixes.append(issue)
    
    # Extract affected components
    components = set()
    for issue in context.jira_issues:
        components.update(issue.components)
    
    # Add components from changed files
    for pr in context.bitbucket_prs:
        for file_path in pr.changed_files:
            if "/" in file_path:
                component = file_path.split("/")[0]
                components.add(component)
    
    context.affected_components = list(components)
    
    return context


async def generate_release_docs(state: AgentState) -> Dict[str, Any]:
    """Generate release documentation content."""
    try:
        from ..generators.release_notes import generate_release_notes
        
        if not state.context:
            return {
                "error": "No context available for document generation",
                "current_step": "generate_release_docs"
            }
        
        # Generate release notes
        release_notes = await generate_release_notes(state.context)
        
        return {
            "context": state.context.model_copy(update={"release_notes": release_notes}),
            "current_step": "plan_edits"
        }
        
    except Exception as e:
        return {
            "error": f"Error generating release docs: {e}",
            "current_step": "generate_release_docs"
        }


async def plan_file_edits(state: AgentState) -> Dict[str, Any]:
    """Plan the file edits needed for the documentation."""
    try:
        from ..generators.guide_edits import plan_guide_edits
        
        if not state.context:
            return {
                "error": "No context available for planning edits",
                "current_step": "plan_file_edits"
            }
        
        # Plan guide edits
        doc_edits = await plan_guide_edits(state.context)
        
        return {
            "context": state.context.model_copy(update={"doc_edits": doc_edits}),
            "current_step": "create_branch"
        }
        
    except Exception as e:
        return {
            "error": f"Error planning file edits: {e}",
            "current_step": "plan_file_edits"
        }


async def create_docs_branch(state: AgentState) -> Dict[str, Any]:
    """Create a new branch for the documentation changes."""
    try:
        # This would typically involve Git operations
        # For now, just return success
        return {
            "current_step": "apply_edits"
        }
        
    except Exception as e:
        return {
            "error": f"Error creating docs branch: {e}",
            "current_step": "create_docs_branch"
        }


async def apply_file_edits(state: AgentState) -> Dict[str, Any]:
    """Apply the planned file edits."""
    try:
        if not state.context or not state.context.doc_edits:
            return {
                "error": "No file edits to apply",
                "current_step": "apply_file_edits"
            }
        
        # Convert doc edits to the format expected by the PR tool
        doc_edits_data = [edit.model_dump() for edit in state.context.doc_edits]
        
        return {
            "doc_edits": doc_edits_data,
            "current_step": "open_pr"
        }
        
    except Exception as e:
        return {
            "error": f"Error applying file edits: {e}",
            "current_step": "apply_file_edits"
        }


async def open_pr(state: AgentState) -> Dict[str, Any]:
    """Open a PR with the documentation changes."""
    try:
        docs_pr_tool = DocsPRTool()
        
        result = await docs_pr_tool._arun(
            doc_edits=state.doc_edits or [],
            version=state.version,
            pr_title=f"Docs: Release {state.version}",
            pr_description=f"Automated documentation updates for release {state.version}",
            labels=settings.release_labels.split(","),
            assignees=settings.pr_assignees.split(",")
        )
        
        if result.get("error"):
            return {
                "error": result["error"],
                "current_step": "open_pr"
            }
        
        return {
            "pr_url": result.get("pr_url"),
            "pr_number": result.get("pr_number"),
            "generated_files": result.get("created_files", []),
            "current_step": "review"
        }
        
    except Exception as e:
        return {
            "error": f"Error opening PR: {e}",
            "current_step": "open_pr"
        }


async def reviewer_reflection(state: AgentState) -> Dict[str, Any]:
    """Review the generated PR and provide feedback."""
    try:
        # This would typically involve reviewing the PR content
        # For now, just return success
        return {
            "current_step": "completed",
            "completed_at": "2024-01-01T00:00:00Z"
        }
        
    except Exception as e:
        return {
            "error": f"Error in reviewer reflection: {e}",
            "current_step": "reviewer_reflection"
        }

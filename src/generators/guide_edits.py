"""Generator for planning guide edits."""

from typing import List
from ..schemas import ReleaseContext, DocEdit


async def plan_guide_edits(context: ReleaseContext) -> List[DocEdit]:
    """Plan the guide edits needed based on the release context."""
    
    doc_edits = []
    
    # Create release notes file
    if context.release_notes:
        doc_edits.append(DocEdit(
            file_path=f"docs/releases/{context.version}.md",
            operation="create",
            content=context.release_notes,
            metadata={
                "version": context.version,
                "type": "release_notes"
            }
        ))
    
    # Update changelog if there are changes
    if context.jira_issues or context.bitbucket_prs:
        changelog_entry = generate_changelog_entry(context)
        doc_edits.append(DocEdit(
            file_path="docs/CHANGELOG.md",
            operation="update",
            content=changelog_entry,
            metadata={
                "version": context.version,
                "type": "changelog_entry"
            }
        ))
    
    # Plan component-specific guide updates
    for component in context.affected_components:
        guide_edit = plan_component_guide_update(component, context)
        if guide_edit:
            doc_edits.append(guide_edit)
    
    return doc_edits


def generate_changelog_entry(context: ReleaseContext) -> str:
    """Generate a changelog entry for the release."""
    
    entry = f"## [{context.version}] - {context.release_branch}\n\n"
    
    if context.new_features:
        entry += "### Added\n"
        for issue in context.new_features:
            entry += f"- {issue.summary} ({issue.key})\n"
        entry += "\n"
    
    if context.bug_fixes:
        entry += "### Fixed\n"
        for issue in context.bug_fixes:
            entry += f"- {issue.summary} ({issue.key})\n"
        entry += "\n"
    
    if context.breaking_changes:
        entry += "### Breaking Changes\n"
        for issue in context.breaking_changes:
            entry += f"- {issue.summary} ({issue.key})\n"
        entry += "\n"
    
    # Add PR references
    if context.bitbucket_prs:
        entry += "### Pull Requests\n"
        for pr in context.bitbucket_prs:
            entry += f"- [{pr.title}]({pr.links.get('html', {}).get('href', '#')}) (#{pr.id})\n"
        entry += "\n"
    
    return entry


def plan_component_guide_update(component: str, context: ReleaseContext) -> DocEdit:
    """Plan a guide update for a specific component."""
    
    # Map components to guide files
    component_guide_map = {
        "api": "docs/api-guide.md",
        "ui": "docs/ui-guide.md",
        "sdk": "docs/sdk-guide.md",
        "config": "docs/configuration.md",
        "migrations": "docs/migrations.md"
    }
    
    guide_file = component_guide_map.get(component.lower())
    if not guide_file:
        return None
    
    # Find relevant issues for this component
    component_issues = [
        issue for issue in context.jira_issues
        if component.lower() in [comp.lower() for comp in issue.components]
    ]
    
    if not component_issues:
        return None
    
    # Generate update content
    update_content = generate_component_update_content(component, component_issues, context)
    
    return DocEdit(
        file_path=guide_file,
        operation="update",
        content=update_content,
        metadata={
            "component": component,
            "version": context.version,
            "type": "component_update"
        }
    )


def generate_component_update_content(component: str, issues: List, context: ReleaseContext) -> str:
    """Generate update content for a component guide."""
    
    content = f"## Updates in {context.version}\n\n"
    
    # Group issues by type
    features = [issue for issue in issues if issue.issue_type.lower() in ["story", "feature"]]
    bugs = [issue for issue in issues if issue.issue_type.lower() in ["bug", "defect"]]
    breaking = [issue for issue in issues if issue.breaking_change]
    
    if features:
        content += "### New Features\n"
        for issue in features:
            content += f"- **{issue.summary}** ({issue.key})\n"
            if issue.changelog:
                content += f"  - {issue.changelog}\n"
        content += "\n"
    
    if bugs:
        content += "### Bug Fixes\n"
        for issue in bugs:
            content += f"- **{issue.summary}** ({issue.key})\n"
        content += "\n"
    
    if breaking:
        content += "### Breaking Changes\n"
        for issue in breaking:
            content += f"- **{issue.summary}** ({issue.key})\n"
            content += f"  - ⚠️ **Action Required**: {issue.changelog or 'See issue for details'}\n"
        content += "\n"
    
    return content

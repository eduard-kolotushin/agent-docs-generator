"""Prompt template for generating release notes."""

RELEASE_NOTES_PROMPT = """
You are a technical writer creating release notes for version {version}.

Based on the following information about the release, generate comprehensive release notes in Markdown format.

## Release Information:
- Version: {version}
- Release Branch: {release_branch}
- Base Tag: {base_tag}

## Jira Issues:
{jira_issues}

## Pull Requests:
{bitbucket_prs}

## Commits:
{bitbucket_commits}

## Previous Release Notes (for reference):
{previous_release_notes}

## Instructions:
1. Create a clear, well-structured release notes document
2. Categorize changes into: New Features, Bug Fixes, Breaking Changes, Improvements
3. Include issue numbers and PR links where relevant
4. Highlight breaking changes prominently
5. Add upgrade instructions if there are breaking changes
6. Use consistent formatting and clear language
7. Include a summary of affected components

## Output Format:
```markdown
# Release {version}

## Summary
Brief overview of the release highlights.

## New Features
- Feature 1 (PROJ-123)
- Feature 2 (PROJ-456)

## Bug Fixes
- Fixed issue with X (PROJ-789)
- Resolved problem with Y (PROJ-101)

## Breaking Changes
- **Important**: Changed API endpoint from /old to /new (PROJ-111)
- Removed deprecated function `oldFunction()` (PROJ-222)

## Improvements
- Performance improvements in component Z
- Updated dependencies

## Upgrade Instructions
If there are breaking changes, provide clear upgrade steps.

## Affected Components
- API
- UI
- SDK
- Configuration
```

Generate the release notes now:
"""

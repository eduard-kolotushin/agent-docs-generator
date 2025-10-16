# Release Documentation Agent

An AI-powered agent built with LangGraph that automatically generates and updates documentation for software releases by analyzing data from Jira, Confluence, and Bitbucket.

## Features

- **Automated Data Gathering**: Collects release information from Jira issues, Bitbucket PRs/commits, and Confluence pages
- **Intelligent Analysis**: Categorizes changes into features, bug fixes, and breaking changes
- **Documentation Generation**: Creates comprehensive release notes and updates existing guides
- **PR Automation**: Automatically creates pull requests with documentation updates
- **Dry Run Mode**: Test the agent without making actual changes

## Architecture

The agent uses LangGraph to orchestrate a state machine with the following components:

- **Data Gathering Tools**: Jira, Bitbucket, and Confluence API clients
- **Analysis Engine**: Categorizes and analyzes gathered data
- **Content Generators**: Creates release notes and guide updates using LLM
- **Repository Management**: Handles Git operations and PR creation

## Requirements

- **Python 3.12+** (required for modern async features and type hints)
- Git (for repository operations)
- Access to Atlassian Cloud services (Jira, Confluence, Bitbucket)
- OpenAI API key (or compatible LLM provider)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd release-docs-agent
```

2. Install dependencies (requires Python 3.12+):
```bash
pip install -e .
```

3. Install development dependencies (optional):
```bash
pip install -e ".[dev]"
```

4. Verify installation:
```bash
python test_installation.py
```

## Configuration

1. Copy the environment template:
```bash
cp env.example .env
```

2. Configure your environment variables in `.env`:

```env
# Jira Configuration
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-jira-api-token

# Confluence Configuration
CONFLUENCE_BASE_URL=https://your-domain.atlassian.net
CONFLUENCE_EMAIL=your-email@example.com
CONFLUENCE_API_TOKEN=your-confluence-api-token

# Bitbucket Configuration
BITBUCKET_WORKSPACE=your-workspace
BITBUCKET_REPO_SLUG=your-main-repo
BITBUCKET_USERNAME=your-username
BITBUCKET_APP_PASSWORD=your-app-password

# Docs Repository (if different from main repo)
DOCS_WORKSPACE=your-workspace
DOCS_REPO_SLUG=your-docs-repo

# LLM Configuration
OPENAI_API_KEY=your-openai-api-key

# Optional Configuration
DRY_RUN=false
BASE_TAG=
RELEASE_LABELS=breaking,docs
PR_ASSIGNEES=team-docs
```

### API Token Setup

#### Jira API Token
1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Create a new API token
3. Use your email and the API token for authentication

#### Confluence API Token
1. Use the same API token as Jira (if using the same Atlassian account)
2. Or create a separate token following the same process

#### Bitbucket App Password
1. Go to [Bitbucket App Passwords](https://bitbucket.org/account/settings/app-passwords/)
2. Create a new app password with repository read/write permissions
3. Use your username and the app password for authentication

## Usage

### Basic Usage

Run the agent for a specific release:

```bash
python -m src.app.main --release release/1.2.3
```

### Dry Run Mode

Test the agent without making actual changes:

```bash
python -m src.app.main --release release/1.2.3 --dry-run
```

### Advanced Options

```bash
python -m src.app.main \
  --release release/1.2.3 \
  --base-tag v1.2.2 \
  --labels "breaking,docs,release" \
  --assignees "team-docs,product-manager" \
  --dry-run
```

### Command Line Options

- `--release`: Release branch name (e.g., `release/1.2.3`)
- `--base-tag`: Base tag to compare against (optional)
- `--dry-run`: Run in dry-run mode (no PR creation)
- `--labels`: Comma-separated labels for the PR
- `--assignees`: Comma-separated assignees for the PR

## How It Works

1. **Validation**: Validates the release branch format and extracts version
2. **Data Gathering**: Parallel collection of data from:
   - Jira issues with the specified fix version
   - Bitbucket PRs targeting the release branch
   - Bitbucket commits in the release branch
   - Confluence pages for context and reference
3. **Analysis**: Categorizes issues into features, bug fixes, and breaking changes
4. **Generation**: Creates release notes and plans guide updates
5. **Repository Operations**: Creates a new branch, applies changes, and opens a PR

## Generated Documentation

The agent generates several types of documentation:

### Release Notes
- Comprehensive release notes in `docs/releases/{version}.md`
- Categorized by features, bug fixes, and breaking changes
- Includes issue references and PR links

### Changelog Updates
- Updates `docs/CHANGELOG.md` with new entries
- Follows conventional changelog format

### Guide Updates
- Updates component-specific guides based on affected areas
- Maps Jira components to documentation files

## Project Structure

```
src/
├── app/
│   └── main.py              # CLI entrypoint
├── clients/                 # API clients
│   ├── jira_client.py
│   ├── bitbucket_client.py
│   ├── confluence_client.py
│   └── docs_repo_client.py
├── generators/              # Content generators
│   ├── release_notes.py
│   └── guide_edits.py
├── graph/                   # LangGraph definitions
│   └── release_docs_graph.py
├── prompts/                 # Prompt templates
│   └── release_notes_prompt.py
├── tools/                   # LangGraph tools
│   ├── jira_tool.py
│   ├── bitbucket_tool.py
│   ├── confluence_tool.py
│   └── docs_pr_tool.py
├── config.py               # Configuration management
└── schemas.py              # Pydantic models
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/ tests/
isort src/ tests/
```

### Type Checking

```bash
mypy src/
```

## Error Handling

The agent includes comprehensive error handling:

- **API Failures**: Graceful degradation when external APIs are unavailable
- **Validation Errors**: Clear error messages for invalid inputs
- **Git Operations**: Proper cleanup of temporary repositories
- **Partial Failures**: Continues processing even if some data sources fail

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Verify your API tokens and credentials
2. **Branch Not Found**: Ensure the release branch exists in Bitbucket
3. **Repository Access**: Check that you have read/write access to the docs repository
4. **LLM Errors**: Verify your OpenAI API key and quota

### Debug Mode

Enable debug logging by setting the `LOG_LEVEL` environment variable:

```bash
export LOG_LEVEL=DEBUG
python -m src.app.main --release release/1.2.3
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review the logs for error messages
3. Open an issue on GitHub
4. Contact the development team

## Roadmap

- [ ] Support for additional issue trackers (GitHub Issues, Azure DevOps)
- [ ] Integration with more documentation platforms
- [ ] Custom prompt templates
- [ ] Batch processing for multiple releases
- [ ] Webhook support for automated triggering
- [ ] Advanced analytics and reporting

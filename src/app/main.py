"""CLI entrypoint for the release docs agent."""

import asyncio
import re
from datetime import datetime
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..config import settings
from ..graph.release_docs_graph import create_release_docs_graph
from ..schemas import AgentState

console = Console()


def validate_release_branch(release_branch: str) -> str:
    """Validate and extract version from release branch name."""
    # Expected format: release/x.y.z or release/x.y.z-beta
    pattern = r"^release/(\d+\.\d+\.\d+(?:-[a-zA-Z0-9.-]+)?)$"
    match = re.match(pattern, release_branch)
    if not match:
        raise click.BadParameter(
            f"Release branch must be in format 'release/x.y.z' or 'release/x.y.z-beta', got: {release_branch}"
        )
    return match.group(1)


@click.command()
@click.option(
    "--release",
    required=True,
    help="Release branch name (e.g., release/1.2.3)",
    callback=lambda ctx, param, value: validate_release_branch(value) if value else None,
)
@click.option(
    "--base-tag",
    help="Base tag to compare against (e.g., v1.2.2). If not provided, will use the previous tag.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Run in dry-run mode (don't create PR, write to ./out/ instead)",
)
@click.option(
    "--labels",
    help="Comma-separated labels for the PR",
    default="breaking,docs",
)
@click.option(
    "--assignees",
    help="Comma-separated assignees for the PR",
    default="team-docs",
)
def cli(release: str, base_tag: Optional[str], dry_run: bool, labels: str, assignees: str):
    """Generate documentation updates for a release."""
    # Override settings with CLI options
    if base_tag:
        settings.base_tag = base_tag
    if dry_run:
        settings.dry_run = True
    if labels:
        settings.release_labels = labels
    if assignees:
        settings.pr_assignees = assignees
    
    # Create initial state
    state = AgentState(
        release_branch=f"release/{release}",
        version=release,
        base_tag=base_tag,
        dry_run=dry_run,
    )
    
    console.print(f"[bold blue]Release Documentation Agent[/bold blue]")
    console.print(f"Release: {state.release_branch}")
    console.print(f"Version: {state.version}")
    console.print(f"Base Tag: {state.base_tag or 'auto-detect'}")
    console.print(f"Dry Run: {state.dry_run}")
    console.print()
    
    # Run the agent
    asyncio.run(run_agent(state))


async def run_agent(state: AgentState) -> None:
    """Run the release docs agent."""
    try:
        # Create the graph
        graph = create_release_docs_graph()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Processing release...", total=None)
            
            # Run the graph
            result = await graph.ainvoke(state.dict())
            
            progress.update(task, description="✅ Processing complete!")
        
        # Display results
        if result.get("error"):
            console.print(f"[bold red]Error:[/bold red] {result['error']}")
            return
        
        if result.get("pr_url"):
            console.print(f"[bold green]PR Created:[/bold green] {result['pr_url']}")
        elif result.get("dry_run"):
            console.print(f"[bold green]Dry run complete![/bold green] Files written to ./out/")
        
        if result.get("generated_files"):
            console.print(f"[bold blue]Generated files:[/bold blue]")
            for file_path in result["generated_files"]:
                console.print(f"  - {file_path}")
        
        if result.get("warnings"):
            console.print(f"[bold yellow]Warnings:[/bold yellow]")
            for warning in result["warnings"]:
                console.print(f"  - {warning}")
                
    except Exception as e:
        console.print(f"[bold red]Fatal error:[/bold red] {e}")
        raise


if __name__ == "__main__":
    cli()

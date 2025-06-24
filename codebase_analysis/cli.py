"""Command-line interface for the analysis tool."""
from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Optional

import click
from git import Repo

from .agents import ParserAgent, PerformanceAgent, SecurityAgent
from .logging_utils import setup_logging
from .orchestrator import Orchestrator


@click.command()
@click.option("--repo", "repo_url", required=True, help="GitHub URL or local path to repo")
@click.option("--output", "output_path", default="report", help="Base path (without extension) for report files")
@click.option("--formats", default="json,html", help="Comma-separated list of report formats: json,html,md,pdf,docx")
@click.option("--clean/--no-clean", default=True, help="Clean up cloned repo directory afterwards")
def cli(repo_url: str, output_path: str, formats: str, clean: bool) -> None:  # pragma: no cover
    """Analyze a repository and generate a report."""
    setup_logging()

    # Prepare repo path
    tmp_dir: Optional[tempfile.TemporaryDirectory[str]] = None
    if Path(repo_url).exists():
        repo_path = Path(repo_url).resolve()
    else:
        tmp_dir = tempfile.TemporaryDirectory()
        logging.info(f"[bold cyan]INFO[/bold cyan] Cloning {repo_url}...")
        Repo.clone_from(repo_url, tmp_dir.name)
        repo_path = Path(tmp_dir.name)

    orchestrator = Orchestrator(repo_path)
    orchestrator.register_agent(ParserAgent)
    orchestrator.register_agent(SecurityAgent)
    orchestrator.register_agent(PerformanceAgent)

    fmt_list = [f.strip() for f in formats.split(',') if f.strip()]
    orchestrator.run(Path(output_path), formats=fmt_list)
    logging.info(f"[bold green]SUCCESS[/bold green] Reports generated at base path {output_path} with formats: {', '.join(fmt_list)}")

    if clean and tmp_dir is not None:
        tmp_dir.cleanup() 
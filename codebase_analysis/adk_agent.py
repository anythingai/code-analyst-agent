"""ADK integration layer exposing our analysis as an ADK Agent.

This file lets the project meet the "built with ADK" criterion by wrapping the
existing multi-agent orchestrator inside a single `google.adk` Agent that can be
run with the standard ADK CLI commands:

    # Developer UI
    adk web

    # Terminal interaction
    adk run codebase_analysis.adk_agent

The `analyze_repo` tool uses the existing `Orchestrator` + specialised agents
(ParserAgent, SecurityAgent, PerformanceAgent) to perform the full analysis.
"""
# ruff: noqa: I001

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from git import Repo

# The official Agent Development Kit (https://pypi.org/project/google-adk/)
try:
    from google.adk.agents import Agent  # type: ignore
except ImportError as exc:  # pragma: no cover – optional runtime dependency
    raise ImportError(
        "google-adk must be installed to use the ADK integration: `pip install google-adk`"
    ) from exc

from .agents import ParserAgent, PerformanceAgent, SecurityAgent
from .orchestrator import Orchestrator


# ---------------------------------------------------------------------------
# Tool function – ADK will surface this as an external capability the agent
# can invoke when asked to analyse a repository.
# ---------------------------------------------------------------------------

def analyze_repo(repo_url: str, formats: list[str] | None = None) -> dict[str, Any]:
    """Clone (if necessary) a repository, run the orchestrator and return results.

    Parameters
    ----------
    repo_url : str
        Either a local filesystem path or a remote HTTPS / Git URL.
    formats : list[str] | None
        Output report formats (e.g. ["json", "html"]). Defaults to JSON only
        for quick interactive sessions.
    """

    tmp_ctx: tempfile.TemporaryDirectory[str] | None = None

    # ---------------- Determine repo path ----------------
    path = Path(repo_url).expanduser()
    if path.exists():
        repo_path = path.resolve()
    else:
        tmp_ctx = tempfile.TemporaryDirectory()
        Repo.clone_from(repo_url, tmp_ctx.name)
        repo_path = Path(tmp_ctx.name)

    # ---------------- Run analysis via our orchestrator ----------------
    orchestrator = Orchestrator(repo_path)
    orchestrator.register_agent(ParserAgent)
    orchestrator.register_agent(SecurityAgent)
    orchestrator.register_agent(PerformanceAgent)

    # Use a temporary directory for outputs; the caller can decide whether to
    # persist them by inspecting the return value.
    out_dir = Path(tempfile.mkdtemp()) / "adk_report"
    results = orchestrator.run(out_dir, formats=formats or ["json"])

    # Clean up cloned repo if we created one.
    if tmp_ctx is not None:
        tmp_ctx.cleanup()

    return results


# ---------------------------------------------------------------------------
# Root agent definition – exposed to the ADK runtime.
# ---------------------------------------------------------------------------

root_agent = Agent(
    name="code_analyst_root",
    model="gemini-2.0-flash",  # Lightweight, change to 2.5-pro for deep dives
    description=(
        "Performs comprehensive codebase analysis using specialised internal"
        " agents for parsing, security and performance."
    ),
    instruction=(
        "When given a repository URL or local path, call the `analyze_repo` tool"
        " to run the full analysis workflow and present a concise summary of the"
        " findings."
    ),
    tools=[analyze_repo],
)


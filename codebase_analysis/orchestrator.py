"""Orchestrator Agent — coordinates sub-agents and merges their outputs."""
from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import TYPE_CHECKING
from typing import Any

from .report.generator import ReportGenerator

if TYPE_CHECKING:
    from pathlib import Path

    from .agents.base import Agent


@dataclass
class Orchestrator:
    """Main orchestrator handling the full analysis workflow."""

    repo_path: Path
    agents: list[Agent] = field(default_factory=list)

    def register_agent(self, agent_cls: type[Agent], **kwargs: Any) -> None:
        """Instantiate and register an agent class."""
        agent = agent_cls(self.repo_path, **kwargs)
        self.agents.append(agent)

    def run(self, output_path: Path, formats: list[str] | None = None) -> dict[str, Any]:
        """Run all registered agents and consolidate results into a report.

        Parameters
        ----------
        output_path : Path
            Path **without extension** indicating where to write reports.
        formats : list[str] | None
            Report formats to generate, forwarded to ``ReportGenerator``.
        """

        results: dict[str, Any] = {}
        for agent in self.agents:
            results[agent.name] = agent.run()

        # Generate aggregated report
        generator = ReportGenerator()
        generator.generate(output_path, results, formats=formats)

        return results

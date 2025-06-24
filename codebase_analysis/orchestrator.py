"""Orchestrator Agent — coordinates sub-agents and merges their outputs."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Type

from .agents.base import Agent
from .report.generator import ReportGenerator


@dataclass
class Orchestrator:
    """Main orchestrator handling the full analysis workflow."""

    repo_path: Path
    agents: List[Agent] = field(default_factory=list)

    def register_agent(self, agent_cls: Type[Agent], **kwargs: Any) -> None:
        """Instantiate and register an agent class."""
        agent = agent_cls(self.repo_path, **kwargs)
        self.agents.append(agent)

    def run(self, output_path: Path, formats: List[str] | None = None) -> Dict[str, Any]:
        """Run all registered agents and consolidate results into a report.

        Parameters
        ----------
        output_path : Path
            Path **without extension** indicating where to write reports.
        formats : list[str] | None
            Report formats to generate, forwarded to ``ReportGenerator``.
        """

        results: Dict[str, Any] = {}
        for agent in self.agents:
            results[agent.name] = agent.run()

        # Generate aggregated report
        generator = ReportGenerator()
        generator.generate(output_path, results, formats=formats)

        return results 
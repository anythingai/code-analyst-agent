"""Performance Agent — detects potential performance bottlenecks."""
from __future__ import annotations

import ast
from typing import TYPE_CHECKING
from typing import Any

from .base import Agent

if TYPE_CHECKING:
    from pathlib import Path


class _NestedLoopVisitor(ast.NodeVisitor):
    """AST visitor to count nested loops."""

    def __init__(self) -> None:
        self.nested_loops = 0

    def visit_For(self, node: ast.For) -> None:  # type: ignore[override]
        if any(isinstance(child, ast.For) for child in ast.iter_child_nodes(node)):
            self.nested_loops += 1
        self.generic_visit(node)


class PerformanceAgent(Agent):
    """Analyzes code for performance anti-patterns (simplified)."""

    @property
    def name(self) -> str:  # noqa: D401
        return "performance_issues"

    def _collect_py_files(self) -> list[Path]:
        venv_path = self.repo_path / ".venv"
        return [
            p
            for p in self.repo_path.rglob("*.py")
            if p.is_file() and not p.resolve().is_relative_to(venv_path.resolve())
        ]

    def run(self) -> dict[str, Any]:
        self.logger.info("[bold yellow]PERFORMANCE[/bold yellow] Detecting bottlenecks...")
        issues: list[dict[str, Any]] = []
        for file in self._collect_py_files():
            text = file.read_text(errors="ignore")
            lines = len(text.splitlines())
            if lines > 1000:
                issues.append({
                    "file": str(file),
                    "issue": "Large file",
                    "detail": f"{lines} lines (>1000)",
                })

            try:
                tree = ast.parse(text)
                visitor = _NestedLoopVisitor()
                visitor.visit(tree)
                if visitor.nested_loops:
                    issues.append({
                        "file": str(file),
                        "issue": "Nested loops",
                        "detail": f"{visitor.nested_loops} nested loops detected",
                    })
            except Exception:
                # Skip files with parse errors
                continue
        return {"count": len(issues), "issues": issues}

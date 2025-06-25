"""Parser Agent — builds ASTs and call graphs using CodeUnderstandingTool."""
from __future__ import annotations

import ast
from typing import TYPE_CHECKING
from typing import Any

import networkx as nx

from ..tools.gemini import CodeUnderstandingTool
from .base import Agent

if TYPE_CHECKING:
    from pathlib import Path


class ParserAgent(Agent):
    """Parses source files to produce AST and call graph summaries."""

    @property
    def name(self) -> str:  # noqa: D401
        return "parser_results"

    def _collect_py_files(self) -> list[Path]:
        venv_path = self.repo_path / ".venv"
        return [
            p
            for p in self.repo_path.rglob("*.py")
            if p.is_file() and not p.resolve().is_relative_to(venv_path.resolve())
        ]

    def _build_call_graph(self, files: list[Path]) -> tuple[nx.DiGraph, int]:
        graph: nx.DiGraph = nx.DiGraph()
        total_functions = 0
        for file in files:
            try:
                tree = ast.parse(file.read_text())
            except Exception:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    total_functions += 1
                    func_name = f"{file.name}:{node.name}"
                    graph.add_node(func_name)
                    # naive: add edges for direct function calls inside body
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                            graph.add_edge(func_name, child.func.id)
        return graph, total_functions

    def run(self) -> dict[str, Any]:
        py_files = self._collect_py_files()
        self.logger.info(f"[bold]PARSER[/bold] Parsing {len(py_files):,} files...")
        graph, total_functions = self._build_call_graph(py_files)

        gemini_tool = CodeUnderstandingTool()
        gemini_summary = gemini_tool.analyze_code(py_files)

        return {
            "file_count": len(py_files),
            "function_count": total_functions,
            "call_graph_nodes": graph.number_of_nodes(),
            "call_graph_edges": graph.number_of_edges(),
            **gemini_summary,
        }

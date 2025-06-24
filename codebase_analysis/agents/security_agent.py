"""Security Agent — scans code for known vulnerabilities and insecure patterns."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from .base import Agent
from ..tools.cve import CVEChecker

# simplistic insecure imports mapping
INSECURE_IMPORTS = {
    "pickle": "Deserialization vulnerability risk",
    "subprocess": "Command injection risk if unsanitized inputs",
}


class SecurityAgent(Agent):
    """Detects potential security issues by static heuristics (placeholder)."""

    @property
    def name(self) -> str:  # noqa: D401
        return "security_findings"

    def _collect_py_files(self) -> List[Path]:
        venv_path = self.repo_path / ".venv"
        return [
            p
            for p in self.repo_path.rglob("*.py")
            if p.is_file() and not p.resolve().is_relative_to(venv_path.resolve())
        ]

    def run(self) -> Dict[str, Any]:
        self.logger.info("[bold orange3]SECURITY[/bold orange3] Scanning for vulnerabilities...")
        findings: List[Dict[str, str]] = []
        cve_checker = CVEChecker()
        for file in self._collect_py_files():
            text = file.read_text(errors="ignore")
            for imp, desc in INSECURE_IMPORTS.items():
                if re.search(rf"\bimport\s+{imp}\b", text):
                    cve_info = cve_checker.search(imp, max_results=3)
                    findings.append({
                        "file": str(file),
                        "issue": f"Insecure import '{imp}' detected",
                        "detail": desc,
                        "cve_matches": cve_info,
                    })
        return {"count": len(findings), "issues": findings} 
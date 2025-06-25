"""Security Agent — scans code for known vulnerabilities and insecure patterns."""
from __future__ import annotations

import re
from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    from pathlib import Path

from ..tools.bigquery import BigQueryTool
from ..tools.cve import CVEChecker
from .base import Agent

# Enhanced insecure imports mapping with more patterns
INSECURE_IMPORTS = {
    "pickle": "Deserialization vulnerability risk - use json or safer alternatives",
    "subprocess": "Command injection risk if unsanitized inputs - validate all inputs",
    "os.system": "Command injection vulnerability - use subprocess with shell=False",
    "eval": "Code injection vulnerability - never use with untrusted input",
    "exec": "Code execution vulnerability - avoid or sanitize carefully",
    "input": "Potential injection if used with eval/exec - validate input",
    "urllib.request.urlopen": "SSRF and certificate validation issues - use requests library",
    "ssl._create_unverified_context": "Disables SSL verification - major security risk",
    "yaml.load": "Code execution vulnerability - use yaml.safe_load instead",
    "shelve": "Pickle-based storage - deserialization risks",
}

# Regex patterns for additional security issues
SECURITY_PATTERNS = [
    (r"password\s*=\s*['\"][^'\"]+['\"]", "Hardcoded password detected"),
    (r"api_key\s*=\s*['\"][^'\"]+['\"]", "Hardcoded API key detected"),
    (r"secret\s*=\s*['\"][^'\"]+['\"]", "Hardcoded secret detected"),
    (r"token\s*=\s*['\"][^'\"]+['\"]", "Hardcoded token detected"),
    (r"shell\s*=\s*True", "Shell injection risk - subprocess with shell=True"),
    (r"random\.random\(\)", "Weak random number generation - use secrets module"),
    (r"md5\(", "Weak hash algorithm MD5 - use SHA-256 or better"),
    (r"sha1\(", "Weak hash algorithm SHA-1 - use SHA-256 or better"),
    (r"assert\s+", "Assertion statements can be disabled - don't use for security"),
    (r"DEBUG\s*=\s*True", "Debug mode enabled - disable in production"),
]


class SecurityAgent(Agent):
    """Enhanced security agent with BigQuery integration for comprehensive vulnerability analysis."""

    @property
    def name(self) -> str:  # noqa: D401
        return "security_findings"

    def _collect_py_files(self) -> list[Path]:
        venv_path = self.repo_path / ".venv"
        return [
            p
            for p in self.repo_path.rglob("*.py")
            if p.is_file() and not p.resolve().is_relative_to(venv_path.resolve())
        ]

    def _extract_dependencies(self, files: list[Path]) -> list[str]:
        """Extract import statements to identify dependencies."""
        dependencies = set()
        for file in files:
            try:
                content = file.read_text(errors="ignore")
                # Extract import statements
                import_matches = re.findall(r"^\s*(?:from\s+(\S+)|import\s+(\S+))", content, re.MULTILINE)
                for match in import_matches:
                    dep = match[0] or match[1]
                    if dep and not dep.startswith('.'):
                        # Get the top-level package name
                        dependencies.add(dep.split('.')[0])
            except Exception:
                continue  # nosec B112
        return list(dependencies)

    def run(self) -> dict[str, Any]:
        self.logger.info("[bold orange3]SECURITY[/bold orange3] Enhanced security analysis...")
        findings: list[dict[str, Any]] = []

        py_files = self._collect_py_files()
        cve_checker = CVEChecker()
        bigquery_tool = BigQueryTool()

        # Extract dependencies for BigQuery analysis
        dependencies = self._extract_dependencies(py_files)

        # Analyze each file for security issues
        for file in py_files:
            file_findings = self._analyze_file_security(file, cve_checker)
            findings.extend(file_findings)

        # Enhanced analysis using BigQuery
        bigquery_results = {}
        if dependencies:
            self.logger.info(f"Analyzing {len(dependencies)} dependencies with BigQuery...")

            # Get vulnerability trends
            vuln_trends = bigquery_tool.query_vulnerability_trends(dependencies)
            bigquery_results["vulnerability_trends"] = vuln_trends

            # Get dependency risk analysis
            risk_analysis = bigquery_tool.analyze_dependency_risks(dependencies)
            bigquery_results["dependency_risks"] = risk_analysis

            # Add high-risk dependencies to findings
            for risk in risk_analysis.get("risk_analysis", []):
                if risk.get("risk_level") == "HIGH":
                    findings.append({
                        "file": "dependencies",
                        "issue": f"High-risk dependency: {risk['dependency']}",
                        "detail": f"Risk score: {risk['calculated_risk_score']}, "
                                f"Vulnerabilities: {risk['vulnerability_count']}",
                        "severity": "HIGH",
                        "risk_data": risk
                    })

        # Query security patterns
        detected_patterns = [pattern for pattern, _ in SECURITY_PATTERNS]
        pattern_results = bigquery_tool.query_security_patterns(detected_patterns)
        bigquery_results["security_patterns"] = pattern_results

        return {
            "count": len(findings),
            "issues": findings,
            "dependencies_analyzed": len(dependencies),
            "bigquery_analysis": bigquery_results,
            "summary": {
                "critical_issues": len([f for f in findings if f.get("severity") == "CRITICAL"]),
                "high_issues": len([f for f in findings if f.get("severity") == "HIGH"]),
                "medium_issues": len([f for f in findings if f.get("severity") == "MEDIUM"]),
                "low_issues": len([f for f in findings if f.get("severity") == "LOW"]),
            }
        }

    def _analyze_file_security(self, file: Path, cve_checker: CVEChecker) -> list[dict[str, Any]]:
        """Analyze a single file for security issues."""
        findings = []

        try:
            text = file.read_text(errors="ignore")

            # Check for insecure imports
            for import_name, description in INSECURE_IMPORTS.items():
                if re.search(rf"\b{re.escape(import_name)}\b", text):
                    try:
                        cve_info = cve_checker.search(import_name, max_results=3)
                    except Exception:
                        cve_info = []

                    findings.append({
                        "file": str(file),
                        "issue": f"Insecure import '{import_name}' detected",
                        "detail": description,
                        "severity": self._get_severity_for_import(import_name),
                        "cve_matches": cve_info,
                    })

            # Check for security patterns
            for pattern, description in SECURITY_PATTERNS:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    line_number = text[:match.start()].count('\n') + 1
                    findings.append({
                        "file": str(file),
                        "issue": description,
                        "detail": f"Line {line_number}: {match.group().strip()}",
                        "severity": self._get_severity_for_pattern(pattern),
                        "line_number": line_number,
                        "matched_text": match.group().strip()
                    })

        except Exception as e:
            self.logger.warning(f"Error analyzing {file}: {e}")

        return findings

    def _get_severity_for_import(self, import_name: str) -> str:
        """Determine severity level for insecure imports."""
        critical_imports = {"eval", "exec", "os.system"}
        high_imports = {"pickle", "yaml.load", "ssl._create_unverified_context"}

        if import_name in critical_imports:
            return "CRITICAL"
        elif import_name in high_imports:
            return "HIGH"
        else:
            return "MEDIUM"

    def _get_severity_for_pattern(self, pattern: str) -> str:
        """Determine severity level for security patterns."""
        critical_patterns = [r"shell\s*=\s*True", r"DEBUG\s*=\s*True"]
        high_patterns = [r"password\s*=\s*", r"api_key\s*=\s*", r"secret\s*=\s*", r"token\s*=\s*"]

        if any(re.search(cp, pattern) for cp in critical_patterns):
            return "CRITICAL"
        elif any(re.search(hp, pattern) for hp in high_patterns):
            return "HIGH"
        else:
            return "MEDIUM"

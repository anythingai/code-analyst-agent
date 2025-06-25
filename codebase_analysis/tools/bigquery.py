"""BigQuery integration for advanced vulnerability and dependency analysis."""
from __future__ import annotations

import logging
import os
from typing import Any

try:
    from google.cloud import bigquery
except ImportError:
    bigquery = None

LOGGER = logging.getLogger(__name__)


class BigQueryTool:
    """Integrates with BigQuery for advanced vulnerability and dependency analysis."""

    def __init__(self, project: str | None = None, dataset: str = "security_analytics"):
        self.project = project or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.dataset = dataset
        self.client = None

        if not self.project:
            LOGGER.warning("BigQuery project not configured. Set GOOGLE_CLOUD_PROJECT.")
            return

        if bigquery is None:
            LOGGER.warning("BigQuery client not available. Install google-cloud-bigquery.")
            return

        try:
            self.client = bigquery.Client(project=self.project)
            LOGGER.info(f"BigQuery client initialized for project: {self.project}")
        except Exception as exc:
            LOGGER.error(f"Failed to initialize BigQuery client: {exc}")

    def query_vulnerability_trends(self, packages: list[str]) -> dict[str, Any]:
        """Query BigQuery for vulnerability trends in specified packages."""
        if not self.client or bigquery is None:
            return {"error": "BigQuery client not available", "trends": [], "total_packages": 0}

        if not packages:
            return {"trends": [], "total_packages": 0}

        try:
            # Parameterized query to prevent SQL injection
            query = """
                SELECT
                    package_name,
                    COUNT(*) as vulnerability_count,
                    AVG(severity_score) as avg_severity,
                    MAX(discovery_date) as latest_vuln_date
                FROM `{self.project}.{self.dataset}.vulnerabilities`
                WHERE package_name IN UNNEST(@packages)
                GROUP BY package_name
                ORDER BY vulnerability_count DESC
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ArrayQueryParameter("packages", "STRING", packages)
                ]
            )
            query_job = self.client.query(query, job_config=job_config)
            results = []

            for row in query_job:
                results.append({
                    "package": row.package_name,
                    "vulnerability_count": row.vulnerability_count,
                    "avg_severity": float(row.avg_severity) if row.avg_severity else 0.0,
                    "latest_vuln_date": row.latest_vuln_date.isoformat() if row.latest_vuln_date else None
                })

            return {
                "trends": results,
                "total_packages": len(results),
                "query_status": "success"
            }

        except Exception as exc:
            LOGGER.warning(f"BigQuery vulnerability trends query failed: {exc}")
            # Return mock data for demo purposes when table doesn't exist
            if "Table" in str(exc) and "not found" in str(exc):
                mock_results = self._generate_mock_vulnerability_data(packages[:5])
                return {
                    "trends": mock_results,
                    "total_packages": len(mock_results),
                    "query_status": "mock_data",
                    "note": "Using mock data - BigQuery table not configured"
                }
            return {
                "error": f"Query failed: {exc}",
                "trends": [],
                "total_packages": 0
            }

    def analyze_dependency_risks(self, dependencies: list[str]) -> dict[str, Any]:
        """Analyze dependency risk patterns using BigQuery."""
        if not self.client or bigquery is None:
            return {"error": "BigQuery client not available", "risk_analysis": [], "total_dependencies": 0}

        if not dependencies:
            return {"risk_analysis": [], "total_dependencies": 0}

        try:
            # Parameterized query to prevent SQL injection
            query = """
                SELECT
                    d.dependency_name,
                    d.version,
                    COUNT(v.vulnerability_id) as vuln_count,
                    AVG(v.cvss_score) as avg_cvss,
                    MAX(v.publication_date) as latest_vuln,
                    d.download_count_last_month,
                    d.maintenance_score
                FROM `{self.project}.{self.dataset}.dependencies` d
                LEFT JOIN `{self.project}.{self.dataset}.vulnerabilities` v
                    ON d.dependency_name = v.package_name
                WHERE d.dependency_name IN UNNEST(@dependencies)
                GROUP BY d.dependency_name, d.version, d.download_count_last_month, d.maintenance_score
                ORDER BY vuln_count DESC, avg_cvss DESC
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ArrayQueryParameter("dependencies", "STRING", dependencies)
                ]
            )
            query_job = self.client.query(query, job_config=job_config)
            results = []

            for row in query_job:
                risk_score = self._calculate_risk_score(
                    row.vuln_count or 0,
                    row.avg_cvss or 0.0,
                    row.maintenance_score or 0.0
                )

                results.append({
                    "dependency": row.dependency_name,
                    "version": row.version,
                    "vulnerability_count": row.vuln_count or 0,
                    "avg_cvss_score": float(row.avg_cvss) if row.avg_cvss else 0.0,
                    "latest_vulnerability": row.latest_vuln.isoformat() if row.latest_vuln else None,
                    "download_count": row.download_count_last_month or 0,
                    "maintenance_score": float(row.maintenance_score) if row.maintenance_score else 0.0,
                    "calculated_risk_score": risk_score,
                    "risk_level": self._categorize_risk(risk_score)
                })

            return {
                "risk_analysis": results,
                "total_dependencies": len(results),
                "high_risk_count": len([r for r in results if r["risk_level"] == "HIGH"]),
                "query_status": "success"
            }

        except Exception as exc:
            LOGGER.warning(f"BigQuery dependency risk analysis failed: {exc}")
            # Return mock data for demo purposes when table doesn't exist
            if "Table" in str(exc) and "not found" in str(exc):
                mock_results = self._generate_mock_dependency_risks(dependencies)
                return {
                    "risk_analysis": mock_results,
                    "total_dependencies": len(mock_results),
                    "high_risk_count": len([r for r in mock_results if r["risk_level"] == "HIGH"]),
                    "query_status": "mock_data",
                    "note": "Using mock data - BigQuery table not configured"
                }
            return {
                "error": f"Analysis failed: {exc}",
                "risk_analysis": [],
                "total_dependencies": 0
            }

    def _calculate_risk_score(self, vuln_count: int, avg_cvss: float, maintenance_score: float) -> float:
        """Calculate a composite risk score for a dependency."""
        # Normalize inputs
        vuln_weight = min(vuln_count * 10, 100)  # Cap at 100
        cvss_weight = (avg_cvss / 10) * 100  # CVSS is 0-10, normalize to 0-100
        maintenance_weight = (1 - maintenance_score) * 100  # Lower maintenance = higher risk

        # Weighted average: vulnerabilities 50%, CVSS 30%, maintenance 20%
        risk_score = (vuln_weight * 0.5) + (cvss_weight * 0.3) + (maintenance_weight * 0.2)
        return round(risk_score, 2)

    def _categorize_risk(self, risk_score: float) -> str:
        """Categorize risk score into LOW, MEDIUM, HIGH levels."""
        if risk_score >= 70:
            return "HIGH"
        elif risk_score >= 40:
            return "MEDIUM"
        else:
            return "LOW"

    def query_security_patterns(self, code_patterns: list[str]) -> dict[str, Any]:
        """Query for known insecure code patterns."""
        if not self.client or bigquery is None:
            return {"error": "BigQuery client not available", "patterns": [], "total_patterns": 0}

        if not code_patterns:
            return {"patterns": [], "total_patterns": 0}

        try:
            # Parameterized query to prevent SQL injection
            query = """
                SELECT
                    pattern_name,
                    description,
                    severity_level,
                    mitigation_advice,
                    detection_count_last_30_days
                FROM `{self.project}.{self.dataset}.security_patterns`
                WHERE pattern_name IN UNNEST(@patterns)
                ORDER BY severity_level DESC
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ArrayQueryParameter("patterns", "STRING", code_patterns)
                ]
            )
            query_job = self.client.query(query, job_config=job_config)
            results = []

            for row in query_job:
                results.append({
                    "pattern": row.pattern_name,
                    "description": row.description,
                    "severity": row.severity_level,
                    "mitigation": row.mitigation_advice,
                    "detection_count": row.detection_count_last_30_days or 0
                })

            return {
                "patterns": results,
                "total_patterns": len(results),
                "query_status": "success"
            }

        except Exception as exc:
            LOGGER.warning(f"BigQuery security patterns query failed: {exc}")
            # Return mock data for demo purposes when table doesn't exist
            if "Table" in str(exc) and "not found" in str(exc):
                mock_results = self._generate_mock_security_patterns(code_patterns)
                return {
                    "patterns": mock_results,
                    "total_patterns": len(mock_results),
                    "query_status": "mock_data",
                    "note": "Using mock data - BigQuery table not configured"
                }
            return {
                "error": f"Query failed: {exc}",
                "patterns": [],
                "total_patterns": 0
            }

    def _generate_mock_vulnerability_data(self, packages: list[str]) -> list[dict[str, Any]]:
        """Generate mock vulnerability data for demo purposes."""
        import random  # nosec B404
        from datetime import datetime
        from datetime import timedelta

        results = []
        for package in packages:
            vuln_count = random.randint(0, 10)  # nosec B311
            if vuln_count > 0:
                results.append({
                    "package": package,
                    "vulnerability_count": vuln_count,
                    "avg_severity": round(random.uniform(3.0, 9.5), 1),  # nosec B311
                    "latest_vuln_date": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat()  # nosec B311
                })
        return results

    def _generate_mock_dependency_risks(self, dependencies: list[str]) -> list[dict[str, Any]]:
        """Generate mock dependency risk data for demo purposes."""
        import random  # nosec B404

        results = []
        for dep in dependencies[:10]:  # Limit to 10 for demo
            vuln_count = random.randint(0, 5)  # nosec B311
            avg_cvss = round(random.uniform(0.0, 9.0), 1) if vuln_count > 0 else 0.0  # nosec B311
            maintenance_score = round(random.uniform(0.3, 1.0), 2)  # nosec B311
            risk_score = self._calculate_risk_score(vuln_count, avg_cvss, maintenance_score)

            results.append({
                "dependency": dep,
                "version": f"{random.randint(1, 5)}.{random.randint(0, 20)}.{random.randint(0, 10)}",  # nosec B311
                "vulnerability_count": vuln_count,
                "avg_cvss_score": avg_cvss,
                "latest_vulnerability": None,
                "download_count": random.randint(1000, 1000000),  # nosec B311
                "maintenance_score": maintenance_score,
                "calculated_risk_score": risk_score,
                "risk_level": self._categorize_risk(risk_score)
            })
        return results

    def _generate_mock_security_patterns(self, patterns: list[str]) -> list[dict[str, Any]]:
        """Generate mock security pattern data for demo purposes."""
        import random  # nosec B404

        pattern_descriptions = {
            "hardcoded_password": "Password or secret key hardcoded in source code",
            "sql_injection": "Potential SQL injection vulnerability",
            "xss_vulnerability": "Cross-site scripting vulnerability",
            "insecure_deserialization": "Unsafe deserialization of user input",
            "weak_cryptography": "Use of weak or deprecated cryptographic algorithms"
        }

        results = []
        for pattern in patterns[:5]:
            if pattern in pattern_descriptions:
                results.append({
                    "pattern": pattern,
                    "description": pattern_descriptions[pattern],
                    "severity": random.choice(["CRITICAL", "HIGH", "MEDIUM"]),  # nosec B311
                    "mitigation": "Review and fix the security issue according to best practices",
                    "detection_count": random.randint(10, 1000)  # nosec B311
                })
        return results

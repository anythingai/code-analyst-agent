"""Tests for enhanced security agent functionality."""
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from codebase_analysis.agents.security_agent import SecurityAgent


@pytest.fixture
def security_agent(tmp_path):
    """Create a security agent for testing."""
    return SecurityAgent(tmp_path)


def test_extract_dependencies(security_agent, tmp_path):
    """Test dependency extraction from Python files."""
    # Create test files with different import patterns
    file1 = tmp_path / "test1.py"
    file1.write_text("""
import os
import sys
from pathlib import Path
import requests
from flask import Flask
""")

    file2 = tmp_path / "test2.py"
    file2.write_text("""
import numpy as np
from pandas import DataFrame
import tensorflow
""")

    dependencies = security_agent._extract_dependencies([file1, file2])

    expected_deps = {'os', 'sys', 'pathlib', 'requests', 'flask', 'numpy', 'pandas', 'tensorflow'}
    assert set(dependencies) == expected_deps


def test_analyze_file_security_insecure_imports(security_agent, tmp_path):
    """Test detection of insecure imports."""
    test_file = tmp_path / "insecure.py"
    test_file.write_text("""
import pickle
import subprocess
import eval
""")

    with patch('codebase_analysis.agents.security_agent.CVEChecker'):
        mock_cve_instance = Mock()
        mock_cve_instance.search.return_value = []

        findings = security_agent._analyze_file_security(test_file, mock_cve_instance)

    # Should detect pickle and subprocess (eval won't match as it's not a real import)
    import_findings = [f for f in findings if 'import' in f['issue']]
    assert len(import_findings) >= 2

    # Check severity levels
    severities = [f['severity'] for f in import_findings]
    assert 'HIGH' in severities or 'MEDIUM' in severities


def test_analyze_file_security_patterns(security_agent, tmp_path):
    """Test detection of security patterns."""
    test_file = tmp_path / "patterns.py"
    test_file.write_text("""
password = "secret123"
api_key = "sk-1234567890"
subprocess.run(cmd, shell=True)
DEBUG = True
""")

    with patch('codebase_analysis.agents.security_agent.CVEChecker'):
        mock_cve_instance = Mock()
        mock_cve_instance.search.return_value = []

        findings = security_agent._analyze_file_security(test_file, mock_cve_instance)

    # Should detect multiple security patterns
    pattern_findings = [f for f in findings if 'password' in f['issue'] or 'api_key' in f['issue'] or 'shell' in f['issue'] or 'Debug' in f['issue']]
    assert len(pattern_findings) >= 3


def test_get_severity_for_import(security_agent):
    """Test severity assignment for imports."""
    assert security_agent._get_severity_for_import('eval') == 'CRITICAL'
    assert security_agent._get_severity_for_import('exec') == 'CRITICAL'
    assert security_agent._get_severity_for_import('pickle') == 'HIGH'
    assert security_agent._get_severity_for_import('subprocess') == 'MEDIUM'


def test_get_severity_for_pattern(security_agent):
    """Test severity assignment for patterns."""
    # Test with actual pattern strings used in the implementation
    assert security_agent._get_severity_for_pattern("shell=True") == 'CRITICAL'
    assert security_agent._get_severity_for_pattern("password=") == 'HIGH'
    assert security_agent._get_severity_for_pattern("md5(") == 'MEDIUM'


def test_security_agent_run_integration(security_agent, tmp_path):
    """Test the complete security agent run method."""
    # Create test files
    file1 = tmp_path / "test.py"
    file1.write_text("""
import pickle
import requests
password = "secret"
""")

    with patch('codebase_analysis.agents.security_agent.CVEChecker'), \
         patch('codebase_analysis.agents.security_agent.BigQueryTool') as mock_bq:

        # Mock CVE checker
        mock_cve_instance = Mock()
        mock_cve_instance.search.return_value = []

        # Mock BigQuery tool
        mock_bq_instance = Mock()
        mock_bq_instance.query_vulnerability_trends.return_value = {
            'trends': [],
            'total_packages': 0
        }
        mock_bq_instance.analyze_dependency_risks.return_value = {
            'risk_analysis': [],
            'total_dependencies': 0
        }
        mock_bq_instance.query_security_patterns.return_value = {
            'patterns': [],
            'total_patterns': 0
        }
        mock_bq.return_value = mock_bq_instance

        result = security_agent.run()

    assert 'count' in result
    assert 'issues' in result
    assert 'dependencies_analyzed' in result
    assert 'bigquery_analysis' in result
    assert 'summary' in result

    # Should have detected some issues
    assert result['count'] > 0

    # Should have analyzed dependencies
    assert result['dependencies_analyzed'] > 0

    # Summary should categorize issues
    summary = result['summary']
    assert all(key in summary for key in ['critical_issues', 'high_issues', 'medium_issues', 'low_issues'])


def test_security_agent_empty_repository(security_agent):
    """Test security agent with empty repository."""
    with patch('codebase_analysis.agents.security_agent.CVEChecker'), \
         patch('codebase_analysis.agents.security_agent.BigQueryTool') as mock_bq:

        # Mock BigQuery tool
        mock_bq_instance = Mock()
        mock_bq_instance.query_vulnerability_trends.return_value = {
            'trends': [],
            'total_packages': 0
        }
        mock_bq_instance.analyze_dependency_risks.return_value = {
            'risk_analysis': [],
            'total_dependencies': 0
        }
        mock_bq_instance.query_security_patterns.return_value = {
            'patterns': [],
            'total_patterns': 0
        }
        mock_bq.return_value = mock_bq_instance

        result = security_agent.run()

    assert result['count'] == 0
    assert result['dependencies_analyzed'] == 0
    assert all(count == 0 for count in result['summary'].values())

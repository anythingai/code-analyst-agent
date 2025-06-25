"""Tests for BigQuery integration."""
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from codebase_analysis.tools.bigquery import BigQueryTool


@pytest.fixture
def mock_bigquery_client():
    """Mock BigQuery client for testing."""
    with patch('codebase_analysis.tools.bigquery.bigquery') as mock_bq:
        mock_client = Mock()
        mock_bq.Client.return_value = mock_client
        yield mock_client


def test_bigquery_tool_init_no_project():
    """Test BigQueryTool initialization without project."""
    with patch.dict('os.environ', {}, clear=True):
        tool = BigQueryTool()
        assert tool.client is None
        assert tool.project is None


def test_bigquery_tool_init_with_project(mock_bigquery_client):
    """Test BigQueryTool initialization with project."""
    with patch.dict('os.environ', {'GOOGLE_CLOUD_PROJECT': 'test-project'}):
        tool = BigQueryTool()
        assert tool.project == 'test-project'
        assert tool.client == mock_bigquery_client


def test_query_vulnerability_trends_no_client():
    """Test vulnerability trends query without client."""
    tool = BigQueryTool()
    result = tool.query_vulnerability_trends(['test-package'])
    assert result['error'] == 'BigQuery client not available'


def test_query_vulnerability_trends_empty_packages(mock_bigquery_client):
    """Test vulnerability trends query with empty packages."""
    with patch.dict('os.environ', {'GOOGLE_CLOUD_PROJECT': 'test-project'}):
        tool = BigQueryTool()
        result = tool.query_vulnerability_trends([])
        assert result['trends'] == []
        assert result['total_packages'] == 0


def test_query_vulnerability_trends_success(mock_bigquery_client):
    """Test successful vulnerability trends query."""
    # Mock query results
    mock_row = Mock()
    mock_row.package_name = 'test-package'
    mock_row.vulnerability_count = 5
    mock_row.avg_severity = 7.5
    mock_row.latest_vuln_date = None

    mock_job = Mock()
    mock_job.__iter__ = Mock(return_value=iter([mock_row]))
    mock_bigquery_client.query.return_value = mock_job

    with patch.dict('os.environ', {'GOOGLE_CLOUD_PROJECT': 'test-project'}):
        tool = BigQueryTool()
        result = tool.query_vulnerability_trends(['test-package'])

        assert result['query_status'] == 'success'
        assert len(result['trends']) == 1
        assert result['trends'][0]['package'] == 'test-package'
        assert result['trends'][0]['vulnerability_count'] == 5
        assert result['trends'][0]['avg_severity'] == 7.5


def test_analyze_dependency_risks_success(mock_bigquery_client):
    """Test successful dependency risk analysis."""
    # Mock query results
    mock_row = Mock()
    mock_row.dependency_name = 'test-dep'
    mock_row.version = '1.0.0'
    mock_row.vuln_count = 3
    mock_row.avg_cvss = 6.0
    mock_row.latest_vuln = None
    mock_row.download_count_last_month = 1000
    mock_row.maintenance_score = 0.8

    mock_job = Mock()
    mock_job.__iter__ = Mock(return_value=iter([mock_row]))
    mock_bigquery_client.query.return_value = mock_job

    with patch.dict('os.environ', {'GOOGLE_CLOUD_PROJECT': 'test-project'}):
        tool = BigQueryTool()
        result = tool.analyze_dependency_risks(['test-dep'])

        assert result['query_status'] == 'success'
        assert len(result['risk_analysis']) == 1
        assert result['risk_analysis'][0]['dependency'] == 'test-dep'
        assert result['risk_analysis'][0]['risk_level'] in ['LOW', 'MEDIUM', 'HIGH']


def test_calculate_risk_score():
    """Test risk score calculation."""
    with patch.dict('os.environ', {'GOOGLE_CLOUD_PROJECT': 'test-project'}):
        tool = BigQueryTool()

        # High risk scenario
        score = tool._calculate_risk_score(10, 9.0, 0.1)
        assert score >= 70  # Should be HIGH risk

        # Low risk scenario
        score = tool._calculate_risk_score(0, 2.0, 0.9)
        assert score < 40  # Should be LOW risk


def test_categorize_risk():
    """Test risk categorization."""
    with patch.dict('os.environ', {'GOOGLE_CLOUD_PROJECT': 'test-project'}):
        tool = BigQueryTool()

        assert tool._categorize_risk(80) == 'HIGH'
        assert tool._categorize_risk(50) == 'MEDIUM'
        assert tool._categorize_risk(30) == 'LOW'


def test_query_security_patterns_success(mock_bigquery_client):
    """Test successful security patterns query."""
    # Mock query results
    mock_row = Mock()
    mock_row.pattern_name = 'sql_injection'
    mock_row.description = 'SQL injection vulnerability'
    mock_row.severity_level = 'CRITICAL'
    mock_row.mitigation_advice = 'Use parameterized queries'
    mock_row.detection_count_last_30_days = 15

    mock_job = Mock()
    mock_job.__iter__ = Mock(return_value=iter([mock_row]))
    mock_bigquery_client.query.return_value = mock_job

    with patch.dict('os.environ', {'GOOGLE_CLOUD_PROJECT': 'test-project'}):
        tool = BigQueryTool()
        result = tool.query_security_patterns(['sql_injection'])

        assert len(result['patterns']) == 1
        assert result['patterns'][0]['pattern'] == 'sql_injection'
        assert result['patterns'][0]['severity'] == 'CRITICAL'
        assert result['query_status'] == 'success'
        assert result['total_patterns'] == 1


def test_bigquery_query_exception(mock_bigquery_client):
    """Test BigQuery query exception handling."""
    mock_bigquery_client.query.side_effect = Exception('Query failed')

    with patch.dict('os.environ', {'GOOGLE_CLOUD_PROJECT': 'test-project'}):
        tool = BigQueryTool()
        result = tool.query_vulnerability_trends(['test-package'])

        assert 'error' in result
        assert 'Query failed' in result['error']

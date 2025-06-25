"""Comprehensive tests for the API module."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from codebase_analysis.api import app


class TestAPIComprehensive:
    """Comprehensive tests for the Flask API."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_healthz_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get('/healthz')
        assert response.status_code == 200
        assert response.data == b'ok'

    def test_index_page(self, client):
        """Test web UI index page."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'html' in response.data.lower()

    def test_analyze_missing_repo_url(self, client):
        """Test analyze endpoint with missing repo_url."""
        response = client.post('/analyze',
                             json={},
                             content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'repo_url is required' in data['error']

    @patch('codebase_analysis.api.Path')
    @patch('codebase_analysis.api.Orchestrator')
    def test_analyze_local_repo(self, mock_orchestrator, mock_path, client):
        """Test analyzing a local repository."""
        # Mock path existence
        mock_path_instance = MagicMock()
        mock_path_instance.expanduser.return_value.exists.return_value = True
        mock_path_instance.expanduser.return_value.resolve.return_value = Path('/test/repo')
        mock_path.return_value = mock_path_instance

        # Mock orchestrator
        mock_orch_instance = MagicMock()
        mock_orch_instance.run.return_value = {'parser': {'status': 'success'}}
        mock_orchestrator.return_value = mock_orch_instance

        response = client.post('/analyze',
                             json={'repo_url': '/test/repo'},
                             content_type='application/json')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'results' in data
        assert 'report_files' in data

    @patch('codebase_analysis.api.Repo')
    @patch('codebase_analysis.api.tempfile.TemporaryDirectory')
    @patch('codebase_analysis.api.Orchestrator')
    def test_analyze_remote_repo(self, mock_orchestrator, mock_tempdir, mock_repo, client):
        """Test analyzing a remote repository."""
        # Mock temporary directory
        mock_temp_instance = MagicMock()
        mock_temp_instance.name = '/tmp/test123'
        mock_tempdir.return_value = mock_temp_instance

        # Mock git clone
        mock_repo.clone_from.return_value = None

        # Mock orchestrator
        mock_orch_instance = MagicMock()
        mock_orch_instance.run.return_value = {'security': {'vulnerabilities': []}}
        mock_orchestrator.return_value = mock_orch_instance

        response = client.post('/analyze',
                             json={'repo_url': 'https://github.com/test/repo'},
                             content_type='application/json')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'results' in data
        mock_repo.clone_from.assert_called_once()
        mock_temp_instance.cleanup.assert_called_once()

    def test_analyze_invalid_remote_url(self, client):
        """Test analyzing with invalid remote URL."""
        response = client.post('/analyze',
                             json={'repo_url': 'ftp://invalid.com/repo'},
                             content_type='application/json')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Unsupported repo_url protocol' in data['error']

    @patch('codebase_analysis.api.Repo')
    @patch('codebase_analysis.api.tempfile.TemporaryDirectory')
    def test_analyze_clone_failure(self, mock_tempdir, mock_repo, client):
        """Test handling git clone failure."""
        # Mock temporary directory
        mock_temp_instance = MagicMock()
        mock_temp_instance.name = '/tmp/test123'
        mock_tempdir.return_value = mock_temp_instance

        # Mock git clone failure
        mock_repo.clone_from.side_effect = Exception("Clone failed")

        response = client.post('/analyze',
                             json={'repo_url': 'https://github.com/test/repo'},
                             content_type='application/json')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Failed to clone repo' in data['error']
        mock_temp_instance.cleanup.assert_called_once()

    @patch('codebase_analysis.api.Path')
    @patch('codebase_analysis.api.Orchestrator')
    def test_analyze_custom_output_name(self, mock_orchestrator, mock_path, client):
        """Test analyze with custom output name."""
        # Mock path
        mock_path_instance = MagicMock()
        mock_path_instance.expanduser.return_value.exists.return_value = True
        mock_path.return_value = mock_path_instance

        # Mock orchestrator
        mock_orch_instance = MagicMock()
        mock_orch_instance.run.return_value = {}
        mock_orchestrator.return_value = mock_orch_instance

        response = client.post('/analyze',
                             json={
                                 'repo_url': '/test/repo',
                                 'output': 'custom_report'
                             },
                             content_type='application/json')

        assert response.status_code == 200
        # Verify the output path contains custom name
        call_args = mock_orch_instance.run.call_args
        output_path = call_args[0][0]
        assert 'custom_report' in str(output_path)

    @patch('codebase_analysis.api.Path')
    @patch('codebase_analysis.api.Orchestrator')
    def test_analyze_custom_formats(self, mock_orchestrator, mock_path, client):
        """Test analyze with custom report formats."""
        # Mock path
        mock_path_instance = MagicMock()
        mock_path_instance.expanduser.return_value.exists.return_value = True
        mock_path.return_value = mock_path_instance

        # Mock orchestrator
        mock_orch_instance = MagicMock()
        mock_orch_instance.run.return_value = {}
        mock_orchestrator.return_value = mock_orch_instance

        response = client.post('/analyze',
                             json={
                                 'repo_url': '/test/repo',
                                 'formats': ['pdf', 'docx']
                             },
                             content_type='application/json')

        assert response.status_code == 200
        # Verify formats were passed
        call_args = mock_orch_instance.run.call_args
        assert call_args[1]['formats'] == ['pdf', 'docx']

    @patch('codebase_analysis.api.Path')
    @patch('codebase_analysis.api.Orchestrator')
    def test_analyze_formats_as_string(self, mock_orchestrator, mock_path, client):
        """Test analyze with formats as comma-separated string."""
        # Mock path
        mock_path_instance = MagicMock()
        mock_path_instance.expanduser.return_value.exists.return_value = True
        mock_path.return_value = mock_path_instance

        # Mock orchestrator
        mock_orch_instance = MagicMock()
        mock_orch_instance.run.return_value = {}
        mock_orchestrator.return_value = mock_orch_instance

        response = client.post('/analyze',
                             json={
                                 'repo_url': '/test/repo',
                                 'formats': 'json, html, pdf'
                             },
                             content_type='application/json')

        assert response.status_code == 200
        # Verify formats were parsed correctly
        call_args = mock_orch_instance.run.call_args
        assert call_args[1]['formats'] == ['json', 'html', 'pdf']

    def test_download_report_not_found(self, client):
        """Test downloading non-existent report."""
        response = client.get('/download/nonexistent.json')
        assert response.status_code == 404

    @patch('codebase_analysis.api.REPORT_DIR')
    @patch('codebase_analysis.api.Path')
    def test_download_report_directory_traversal(self, mock_path, mock_report_dir, client):
        """Test protection against directory traversal."""
        mock_report_dir.resolve.return_value = Path('/reports')

        # Try to access file outside report directory
        mock_file_path = MagicMock()
        mock_file_path.resolve.return_value = Path('/etc/passwd')
        mock_file_path.is_file.return_value = True
        mock_path.return_value = mock_file_path

        response = client.get('/download/../../../etc/passwd')
        assert response.status_code == 404

    def test_security_headers(self, client):
        """Test that security headers are set."""
        response = client.get('/healthz')
        assert 'Content-Security-Policy' in response.headers
        assert 'X-Content-Type-Options' in response.headers
        assert response.headers['X-Content-Type-Options'] == 'nosniff'
        assert response.headers['X-Frame-Options'] == 'DENY'

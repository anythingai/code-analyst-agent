"""Test the report generator module."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from codebase_analysis.report.generator import ReportGenerator


class TestReportGenerator:
    """Test the ReportGenerator class."""

    @pytest.fixture
    def sample_results(self):
        """Provide sample analysis results for testing."""
        return {
            "parser": {
                "status": "success",
                "files_analyzed": 10,
                "classes": 5,
                "functions": 20
            },
            "security": {
                "vulnerabilities": [
                    {"type": "hardcoded_password", "severity": "HIGH"},
                    {"type": "sql_injection", "severity": "CRITICAL"}
                ],
                "insecure_imports": ["pickle", "eval"]
            },
            "performance": {
                "issues": [
                    {"type": "nested_loops", "complexity": "O(n^3)"},
                    {"type": "large_file", "lines": 5000}
                ]
            }
        }

    def test_report_generator_init(self):
        """Test ReportGenerator initialization."""
        generator = ReportGenerator()
        assert generator is not None

    def test_generate_json_report(self, tmp_path, sample_results):
        """Test JSON report generation."""
        generator = ReportGenerator()
        output_path = tmp_path / "test_report"

        generator.generate(output_path, sample_results, formats=["json"])

        json_file = Path(f"{output_path}.json")
        assert json_file.exists()

        # Verify content
        with open(json_file) as f:
            data = json.load(f)

        assert "parser" in data
        assert "security" in data
        assert "performance" in data
        assert data["parser"]["files_analyzed"] == 10

    def test_generate_html_report(self, tmp_path, sample_results):
        """Test HTML report generation."""
        generator = ReportGenerator()
        output_path = tmp_path / "test_report"

        generator.generate(output_path, sample_results, formats=["html"])

        html_file = Path(f"{output_path}.html")
        assert html_file.exists()

        # Verify basic HTML structure
        content = html_file.read_text()
        assert "<html" in content
        assert "parser" in content.lower()
        assert "security" in content.lower()

    def test_generate_markdown_report(self, tmp_path, sample_results):
        """Test Markdown report generation."""
        generator = ReportGenerator()
        output_path = tmp_path / "test_report"

        generator.generate(output_path, sample_results, formats=["md"])

        md_file = Path(f"{output_path}.md")
        assert md_file.exists()

        # Verify content
        content = md_file.read_text()
        assert "# Codebase Analysis Report" in content
        assert "## Parser Results" in content or "## parser" in content
        assert "## Security Findings" in content or "## security" in content
        assert "## Performance Issues" in content or "## performance" in content

    @patch('fpdf.FPDF')
    def test_generate_pdf_report(self, mock_fpdf, tmp_path, sample_results):
        """Test PDF report generation."""
        # Mock FPDF instance
        mock_pdf_instance = MagicMock()
        mock_fpdf.return_value = mock_pdf_instance

        generator = ReportGenerator()
        output_path = tmp_path / "test_report"

        generator.generate(output_path, sample_results, formats=["pdf"])

        # Verify FPDF was used
        mock_fpdf.assert_called_once()
        mock_pdf_instance.add_page.assert_called()
        mock_pdf_instance.output.assert_called_once()

    @patch('docx.Document')
    def test_generate_docx_report(self, mock_document, tmp_path, sample_results):
        """Test DOCX report generation."""
        # Mock Document instance
        mock_doc_instance = MagicMock()
        mock_document.return_value = mock_doc_instance

        generator = ReportGenerator()
        output_path = tmp_path / "test_report"

        generator.generate(output_path, sample_results, formats=["docx"])

        # Verify Document was used
        mock_document.assert_called_once()
        mock_doc_instance.add_heading.assert_called()
        mock_doc_instance.save.assert_called_once()

    def test_generate_multiple_formats(self, tmp_path, sample_results):
        """Test generating multiple report formats."""
        generator = ReportGenerator()
        output_path = tmp_path / "test_report"

        generator.generate(output_path, sample_results, formats=["json", "md"])

        assert Path(f"{output_path}.json").exists()
        assert Path(f"{output_path}.md").exists()

    def test_generate_with_metadata(self, tmp_path):
        """Test report generation with metadata."""
        results = {
            "metadata": {
                "repo_url": "https://github.com/test/repo",
                "analysis_date": "2024-01-15",
                "duration": 120
            },
            "parser": {"status": "success"}
        }

        generator = ReportGenerator()
        output_path = tmp_path / "test_report"

        generator.generate(output_path, results, formats=["json"])

        with open(f"{output_path}.json") as f:
            data = json.load(f)

        assert "metadata" in data
        assert data["metadata"]["repo_url"] == "https://github.com/test/repo"

    def test_generate_empty_results(self, tmp_path):
        """Test handling empty results."""
        generator = ReportGenerator()
        output_path = tmp_path / "test_report"

        generator.generate(output_path, {}, formats=["json"])

        json_file = Path(f"{output_path}.json")
        assert json_file.exists()

        with open(json_file) as f:
            data = json.load(f)
        assert data == {}

    def test_generate_default_formats(self, tmp_path, sample_results):
        """Test default format generation when none specified."""
        generator = ReportGenerator()
        output_path = tmp_path / "test_report"

        # Should use default formats when None passed
        generator.generate(output_path, sample_results, formats=None)

        # Check at least JSON is generated (common default)
        assert Path(f"{output_path}.json").exists()

    def test_invalid_format_handling(self, tmp_path, sample_results):
        """Test handling of invalid format."""
        generator = ReportGenerator()
        output_path = tmp_path / "test_report"

        with pytest.raises(ValueError, match="Unsupported report format"):
            generator.generate(output_path, sample_results, formats=["invalid_format"])

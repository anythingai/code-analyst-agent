"""Test the orchestrator module."""
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

from codebase_analysis.agents.base import Agent
from codebase_analysis.orchestrator import Orchestrator


class MockAgent(Agent):
    """Mock agent for testing."""

    @property
    def name(self) -> str:
        """Return agent name."""
        return "mock_agent"

    def run(self) -> dict:
        """Return mock results."""
        return {"status": "success", "data": "mock_data"}


class TestOrchestrator:
    """Test the Orchestrator class."""

    def test_orchestrator_init(self, tmp_path):
        """Test orchestrator initialization."""
        orchestrator = Orchestrator(tmp_path)
        assert orchestrator.repo_path == tmp_path
        assert orchestrator.agents == []

    def test_register_agent(self, tmp_path):
        """Test agent registration."""
        orchestrator = Orchestrator(tmp_path)
        orchestrator.register_agent(MockAgent)

        assert len(orchestrator.agents) == 1
        assert isinstance(orchestrator.agents[0], MockAgent)
        assert orchestrator.agents[0].repo_path == tmp_path

    def test_register_agent_with_kwargs(self, tmp_path):
        """Test agent registration with additional kwargs."""
        orchestrator = Orchestrator(tmp_path)
        orchestrator.register_agent(MockAgent, extra_param="value")

        assert len(orchestrator.agents) == 1

    @patch('codebase_analysis.orchestrator.ReportGenerator')
    def test_run_single_agent(self, mock_report_gen, tmp_path):
        """Test running orchestrator with a single agent."""
        # Setup
        orchestrator = Orchestrator(tmp_path)
        orchestrator.register_agent(MockAgent)

        # Mock report generator
        mock_gen_instance = MagicMock()
        mock_report_gen.return_value = mock_gen_instance

        # Run
        output_path = tmp_path / "test_report"
        results = orchestrator.run(output_path, formats=["json"])

        # Assertions
        assert "mock_agent" in results
        assert results["mock_agent"]["status"] == "success"
        mock_gen_instance.generate.assert_called_once_with(
            output_path, results, formats=["json"]
        )

    @patch('codebase_analysis.orchestrator.ReportGenerator')
    def test_run_multiple_agents(self, mock_report_gen, tmp_path):
        """Test running orchestrator with multiple agents."""
        # Create a second mock agent
        class MockAgent2(Agent):
            @property
            def name(self) -> str:
                return "mock_agent_2"

            def run(self) -> dict:
                return {"status": "complete", "count": 42}

        # Setup
        orchestrator = Orchestrator(tmp_path)
        orchestrator.register_agent(MockAgent)
        orchestrator.register_agent(MockAgent2)

        # Mock report generator
        mock_gen_instance = MagicMock()
        mock_report_gen.return_value = mock_gen_instance

        # Run
        output_path = tmp_path / "test_report"
        results = orchestrator.run(output_path, formats=["json", "html"])

        # Assertions
        assert len(results) == 2
        assert "mock_agent" in results
        assert "mock_agent_2" in results
        assert results["mock_agent"]["status"] == "success"
        assert results["mock_agent_2"]["count"] == 42

        mock_gen_instance.generate.assert_called_once_with(
            output_path, results, formats=["json", "html"]
        )

    @patch('codebase_analysis.orchestrator.ReportGenerator')
    def test_run_with_default_formats(self, mock_report_gen, tmp_path):
        """Test running orchestrator without specifying formats."""
        orchestrator = Orchestrator(tmp_path)
        orchestrator.register_agent(MockAgent)

        mock_gen_instance = MagicMock()
        mock_report_gen.return_value = mock_gen_instance

        output_path = tmp_path / "test_report"
        results = orchestrator.run(output_path)

        # Should pass None for formats
        mock_gen_instance.generate.assert_called_once_with(
            output_path, results, formats=None
        )

    def test_empty_orchestrator_run(self, tmp_path):
        """Test running orchestrator with no agents."""
        orchestrator = Orchestrator(tmp_path)

        with patch('codebase_analysis.orchestrator.ReportGenerator') as mock_report_gen:
            mock_gen_instance = MagicMock()
            mock_report_gen.return_value = mock_gen_instance

            output_path = tmp_path / "test_report"
            results = orchestrator.run(output_path)

            # Should have empty results
            assert results == {}
            mock_gen_instance.generate.assert_called_once()

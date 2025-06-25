import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

from codebase_analysis.adk_agent import analyze_repo
from codebase_analysis.adk_agent import root_agent


def test_analyze_repo_with_local_path():
    """Test analyze_repo with a local path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        (repo_path / ".git").mkdir()

        with patch("codebase_analysis.adk_agent.Orchestrator") as mock_orchestrator:
            mock_orchestrator_instance = MagicMock()
            mock_orchestrator.return_value = mock_orchestrator_instance
            mock_orchestrator_instance.run.return_value = {"status": "success"}

            results = analyze_repo(str(repo_path))

            mock_orchestrator.assert_called_with(repo_path.resolve())
            mock_orchestrator_instance.run.assert_called_once()
            assert results == {"status": "success"}


def test_analyze_repo_with_remote_url():
    """Test analyze_repo with a remote URL."""
    with patch("git.Repo.clone_from") as mock_clone, patch(
        "codebase_analysis.adk_agent.Orchestrator"
    ) as mock_orchestrator:
        mock_orchestrator_instance = MagicMock()
        mock_orchestrator.return_value = mock_orchestrator_instance
        mock_orchestrator_instance.run.return_value = {"status": "cloned_and_success"}

        results = analyze_repo("https://github.com/fake/repo.git")

        mock_clone.assert_called_once()
        mock_orchestrator.assert_called_once()
        mock_orchestrator_instance.run.assert_called_once()
        assert results == {"status": "cloned_and_success"}


def test_root_agent_definition():
    """Test the definition of the root_agent."""
    assert root_agent.name == "code_analyst_root"
    assert root_agent.description is not None
    assert root_agent.instruction is not None
    assert root_agent.tools == [analyze_repo]

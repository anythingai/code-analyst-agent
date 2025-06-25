import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

from click.testing import CliRunner

from codebase_analysis.cli import cli


def test_cli_with_mock_repo_and_orchestrator():
    """Test the CLI with a mocked repository and orchestrator."""
    runner = CliRunner()
    with patch("git.Repo.clone_from") as mock_clone, patch(
        "codebase_analysis.cli.Orchestrator"
    ) as mock_orchestrator:
        mock_orchestrator_instance = MagicMock()
        mock_orchestrator.return_value = mock_orchestrator_instance

        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["REPORT_DIR"] = tmpdir
            result = runner.invoke(
                cli, ["--repo", "https://github.com/fake/repo.git", "--formats", "json"]
            )

            assert result.exit_code == 0
            assert "Cloning https://github.com/fake/repo.git" in result.output
            assert "Reports generated" in result.output
            mock_clone.assert_called_once()
            mock_orchestrator.assert_called_once()
            mock_orchestrator_instance.run.assert_called_once()
            # The first argument to run should be a Path object
            args, kwargs = mock_orchestrator_instance.run.call_args
            assert isinstance(args[0], Path)
            assert kwargs == {"formats": ["json"]}


def test_cli_with_local_directory():
    """Test the CLI with a local directory."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir, patch(
        "codebase_analysis.cli.Orchestrator"
    ) as mock_orchestrator:
        mock_orchestrator_instance = MagicMock()
        mock_orchestrator.return_value = mock_orchestrator_instance
        os.environ["REPORT_DIR"] = tmpdir

        # Create a fake file in the temp dir to act as a repo
        (Path(tmpdir) / ".git").mkdir()

        result = runner.invoke(cli, ["--repo", tmpdir])

        assert result.exit_code == 0
        mock_orchestrator.assert_called_with(Path(tmpdir).resolve())
        mock_orchestrator_instance.run.assert_called_once()


def test_cli_different_options():
    """Test the CLI with different options."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir, patch(
        "codebase_analysis.cli.Orchestrator"
    ) as mock_orchestrator:
        mock_orchestrator_instance = MagicMock()
        mock_orchestrator.return_value = mock_orchestrator_instance
        os.environ["REPORT_DIR"] = tmpdir

        # Create a fake file in the temp dir to act as a repo
        (Path(tmpdir) / ".git").mkdir()

        result = runner.invoke(
            cli,
            [
                "--repo",
                tmpdir,
                "--output",
                "my-report",
                "--formats",
                "html,pdf",
                "--no-clean",
            ],
        )

        assert result.exit_code == 0
        args, kwargs = mock_orchestrator_instance.run.call_args
        assert args[0] == Path(tmpdir) / "my-report"
        assert kwargs == {"formats": ["html", "pdf"]}

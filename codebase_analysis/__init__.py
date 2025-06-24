"""Top-level package for Code Analyst Agent."""

from importlib import metadata

# Load environment variables from .env if present
try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()  # automatically search for .env in current and parent dirs
except ImportError:  # pragma: no cover
    # python-dotenv is optional; if not installed, ignore
    pass

__version__: str = metadata.version("codebase-analysis") if metadata else "0.1.0"

# Re-export public API
from .orchestrator import Orchestrator  # noqa: E402

__all__ = [
    "Orchestrator",
    "__version__",
] 
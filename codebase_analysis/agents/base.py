"""Abstract Agent definition used by all sub-agents."""
from __future__ import annotations

import abc
import logging
from pathlib import Path
from typing import Any, Dict


class Agent(abc.ABC):
    """Base class for all agents."""

    def __init__(self, repo_path: Path, **config: Any) -> None:
        self.repo_path = repo_path
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    @property
    @abc.abstractmethod
    def name(self) -> str:  # noqa: D401
        """Human-readable agent name."""

    @abc.abstractmethod
    def run(self) -> Dict[str, Any]:
        """Execute analysis and return results as a dictionary.""" 
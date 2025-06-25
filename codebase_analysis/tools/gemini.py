"""Wrapper around Gemini models via Vertex AI SDK or Google AI SDK.

This tool provides a flexible `analyze_code` method that sends code snippets
to Gemini for deeper understanding. It prioritizes authentication in this order:
1. Google AI SDK (using GOOGLE_API_KEY)
2. Vertex AI SDK (using GOOGLE_CLOUD_PROJECT and service account)
"""
from __future__ import annotations

import logging
import os
import time
from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    from pathlib import Path

try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    from google.cloud import aiplatform
    from vertexai.generative_models import GenerativeModel
except ImportError:
    aiplatform = None
    GenerativeModel = None

LOGGER = logging.getLogger(__name__)


class CodeUnderstandingTool:
    """Interact with Gemini to get insights about code."""

    def __init__(
        self,
        project: str | None = None,
        location: str = "us-central1",
        model: str = "gemini-1.5-pro",
    ) -> None:
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.project = project or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = location
        self.model = model
        self.mode = self._determine_mode()
        self._initialize_client()

    def _determine_mode(self) -> str:
        if self.api_key and genai:
            LOGGER.info("Using Google AI SDK for Gemini (API Key found).")
            return "google_ai"
        if self.project and aiplatform:
            LOGGER.info("Using Vertex AI SDK for Gemini (Project found).")
            return "vertex_ai"

        # Credentials **must** be provided; otherwise abort early.
        raise RuntimeError(
            "Gemini credentials not configured. Set GOOGLE_API_KEY for the Google AI SDK "
            "or configure GOOGLE_CLOUD_PROJECT with a service-account for Vertex AI."
        )

    def _initialize_client(self) -> None:
        """Initialize the appropriate client based on mode."""
        if self.mode == "google_ai":
            if genai is None:
                raise ImportError("google-generativeai must be installed")
            genai.configure(api_key=self.api_key)  # type: ignore
            self.model_client = genai.GenerativeModel(self.model)  # type: ignore
        else:  # vertex_ai
            if aiplatform is None or GenerativeModel is None:
                raise ImportError("google-cloud-aiplatform must be installed")
            aiplatform.init(project=self.project, location=self.location)  # type: ignore
            self.model_client = GenerativeModel(self.model)  # type: ignore

    def analyze_code(self, files: list[Path]) -> dict[str, Any]:
        """Send a batch of code files to Gemini and get high-level summary."""
        # Gracefully handle repos with no or empty Python files
        if not files:
            return {"gemini_summary": "No Python files found to analyze.", "file_count": 0}

        max_files_env = os.getenv("GEMINI_MAX_FILES", "20")
        max_files = 0 if max_files_env.lower() == "all" else int(max_files_env)
        sample_files = files if max_files == 0 else files[:max_files]

        # Build content with file paths
        file_contents = []
        for f in sample_files:
            try:
                content = f.read_text(errors="ignore")
                if content:
                    file_contents.append(f"### File: {f.name}\n```python\n{content}\n```")
            except Exception as e:
                LOGGER.warning(f"Failed to read {f}: {e}")

        if not file_contents:
            return {"gemini_summary": "Python files were empty; nothing to analyze.", "file_count": 0}

        # Construct a detailed prompt
        newline_join = '\n\n'.join(file_contents[:10])
        prompt = f"""Analyze the following Python codebase and provide:
1. A high-level architectural overview
2. Key patterns and design decisions
3. Potential security concerns
4. Performance considerations
5. Code quality observations

Files analyzed: {len(sample_files)} of {len(files)} total Python files

{newline_join}

Provide a comprehensive but concise analysis."""

        # Retry logic for API calls
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if self.mode == "google_ai":
                    response = self.model_client.generate_content(prompt)
                    return {
                        "gemini_summary": response.text,
                        "file_count": len(files),
                        "analyzed_files": len(sample_files)
                    }
                else:  # vertex_ai
                    response = self.model_client.generate_content(prompt)
                    return {
                        "gemini_summary": response.text,
                        "file_count": len(files),
                        "analyzed_files": len(sample_files)
                    }
            except Exception as e:
                LOGGER.warning(f"Gemini API attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    return {
                        "gemini_summary": f"Gemini analysis failed after {max_retries} attempts: {str(e)}",
                        "file_count": len(files),
                        "analyzed_files": 0,
                        "error": str(e)
                    }
        return {
            "gemini_summary": "Gemini analysis failed due to an unexpected error.",
            "file_count": len(files),
            "analyzed_files": 0,
            "error": "Max retries reached without success."
        }

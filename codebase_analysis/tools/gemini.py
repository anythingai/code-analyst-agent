"""Wrapper around Gemini models via Vertex AI SDK or Google AI SDK.

This tool provides a flexible `analyze_code` method that sends code snippets
to Gemini for deeper understanding. It prioritizes authentication in this order:
1. Google AI SDK (using GOOGLE_API_KEY)
2. Vertex AI SDK (using GOOGLE_CLOUD_PROJECT and service account)
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List

try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    from google.cloud import aiplatform_v1beta1 as aiplatform
except ImportError:
    aiplatform = None

LOGGER = logging.getLogger(__name__)


class CodeUnderstandingTool:
    """Interact with Gemini to get insights about code."""

    def __init__(
        self,
        project: str | None = None,
        location: str = "us-central1",
        model: str = "gemini-1.5-pro-preview",
    ) -> None:
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.project = project or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = location
        self.model = model
        self.mode = self._determine_mode()

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

    def analyze_code(self, files: List[Path]) -> Dict[str, Any]:
        """Send a batch of code files to Gemini and get high-level summary."""
        # Gracefully handle repos with no or empty Python files
        if not files:
            return {"gemini_summary": "No Python files found to analyze."}

        max_files_env = os.getenv("GEMINI_MAX_FILES", "20")
        max_files = 0 if max_files_env.lower() == "all" else int(max_files_env)
        sample_files = files if max_files == 0 else files[:max_files]
        content = "\n\n".join(
            (f.read_text(errors="ignore") or "") for f in sample_files
        ).strip()

        if not content:
            return {"gemini_summary": "Python files were empty; nothing to analyze."}

        if self.mode == "google_ai":
            return self._analyze_with_google_ai(content)
        # Only other possibility is vertex_ai
        return self._analyze_with_vertex_ai(content)

    def _analyze_with_google_ai(self, content: str) -> Dict[str, Any]:
        """Use the Google AI SDK (API Key)."""
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        response = model.generate_content(content)
        return {"gemini_summary": response.text}

    def _analyze_with_vertex_ai(self, content: str) -> Dict[str, Any]:
        """Use the Vertex AI SDK (Service Account)."""
        client = aiplatform.PredictionServiceClient()
        endpoint = client.endpoint_path(
            project=self.project, location=self.location, endpoint=self.model
        )
        response = client.predict(
            endpoint=endpoint,
            instances=[{"content": content}],
            parameters={"temperature": 0.2},
        )
        return {"gemini_summary": response.predictions[0].get("content", "")} 
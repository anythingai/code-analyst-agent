import pytest

from codebase_analysis.tools.gemini import CodeUnderstandingTool


@pytest.fixture(autouse=True)
def _patch_gemini(monkeypatch):
    """Ensure tests never hit real Gemini services.

    * Sets a dummy ``GOOGLE_API_KEY`` so the credential check in
      ``CodeUnderstandingTool._determine_mode`` passes.
    * Stubs ``CodeUnderstandingTool.analyze_code`` to return an empty mapping
      immediately so no network traffic occurs.
    """
    # Provide fake credentials so the tool initialises without error.
    monkeypatch.setenv("GOOGLE_API_KEY", "dummy-key-for-tests")

    # Prevent any accidental remote calls during unit-tests.
    monkeypatch.setattr(CodeUnderstandingTool, "analyze_code", lambda self, files: {}) 
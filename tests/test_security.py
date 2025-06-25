from pathlib import Path

from codebase_analysis.agents.security_agent import SecurityAgent
from codebase_analysis.tools.cve import CVEChecker


def test_security_agent_detects_insecure_import(tmp_path, monkeypatch):
    file = tmp_path / "bad.py"
    file.write_text("""import pickle\n""")

    # avoid external CVE API call
    monkeypatch.setattr(CVEChecker, "search", lambda self, keyword, max_results=10: [])

    agent = SecurityAgent(Path(tmp_path))
    res = agent.run()
    assert res["count"] == 1
    assert any(issue["issue"].startswith("Insecure import") for issue in res["issues"])

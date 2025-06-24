from pathlib import Path

from codebase_analysis.agents.security_agent import SecurityAgent


def test_security_agent_detects_insecure_import(tmp_path):
    file = tmp_path / "bad.py"
    file.write_text("""import pickle\n""")
    agent = SecurityAgent(Path(tmp_path))
    res = agent.run()
    assert res["count"] == 1
    assert any(issue["issue"].startswith("Insecure import") for issue in res["issues"]) 
from pathlib import Path

from codebase_analysis.agents.performance_agent import PerformanceAgent


def test_performance_agent_large_file(tmp_path):
    file = tmp_path / "big.py"
    # create file >1000 lines
    file.write_text("\n".join(["pass"] * 1001))

    agent = PerformanceAgent(Path(tmp_path))
    res = agent.run()
    assert res["count"] == 1
    assert any(issue["issue"] == "Large file" for issue in res["issues"])

from pathlib import Path

from codebase_analysis.agents.parser_agent import ParserAgent


def test_parser_counts(tmp_path):
    # create simple python file
    file = tmp_path / "hello.py"
    file.write_text("""def foo():\n    pass\n""")
    agent = ParserAgent(Path(tmp_path))
    res = agent.run()
    assert res["file_count"] == 1
    assert res["function_count"] == 1 
import json

from regressionproof.compare import compare_revisions
from regressionproof.model import Outcome, RevisionResult, TestCase, TestRun
from regressionproof.report import to_markdown, write_report


def test_report_and_markdown_escaping(tmp_path):
    key = "module::hello|`world`\nnewline"
    base = RevisionResult("main", "a" * 40, (TestRun({key: TestCase(key, Outcome.PASSED)}, 0, 1),))
    head = RevisionResult("topic", "b" * 40, (TestRun({key: TestCase(key, Outcome.FAILED)}, 1, 1),))
    comparison = compare_revisions(base, head)
    result, markdown = write_report(comparison, tmp_path / "out")
    data = json.loads(result.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
    assert data["status"] == "regression"
    assert data["tests"]["regressions"][0]["key"] == key
    assert "hello\\|\\`world\\` newline" in markdown.read_text(encoding="utf-8")
    assert to_markdown(comparison).startswith("# RegressionProof")

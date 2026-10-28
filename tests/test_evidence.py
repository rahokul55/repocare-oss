"""Confidence and continuity checks for cross-revision test comparisons."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from regressionproof.cli import main
from regressionproof.compare import compare_revisions
from regressionproof.model import Outcome, RevisionResult, TestCase, TestRun
from regressionproof.report import to_html, to_payload


def revision(ref: str, *runs: dict[str, Outcome]) -> RevisionResult:
    return RevisionResult(
        ref, "f" * 40,
        tuple(TestRun({key: TestCase(key, result) for key, result in tests.items()}, 0, 0.1)
              for tests in runs),
    )


def _xml(path: Path, *cases: str) -> Path:
    path.write_text('<testsuite>' + ''.join(f'<testcase name="{name}"/>' for name in cases)
                    + '</testsuite>', encoding='utf-8')
    return path


def test_empty_identity_intersection_is_insufficient_not_a_success_proof():
    comparison = compare_revisions(revision("base", {"old": Outcome.PASSED}),
                                   revision("head", {"new": Outcome.PASSED}))
    evidence = comparison.evidence
    assert not comparison.has_new_failure
    assert evidence.quality == "insufficient"
    assert evidence.overlap_percent == 0
    assert evidence.shared_tests == 0
    assert evidence.added_tests == 1
    assert evidence.removed_tests == 1
    assert "No shared test identities" in evidence.warnings[0]
    assert to_payload(comparison)["evidence"]["quality"] == "insufficient"
    assert "Evidence quality" in to_html(comparison)


def test_partial_overlap_and_warning_for_removed_test():
    comparison = compare_revisions(
        revision("base", {"a": Outcome.PASSED, "b": Outcome.PASSED}),
        revision("head", {"a": Outcome.PASSED, "c": Outcome.PASSED}),
    )
    evidence = comparison.evidence
    assert evidence.shared_tests == 1
    assert evidence.overlap_percent == 50
    assert evidence.quality == "partial"
    assert evidence.added_tests == 1
    assert evidence.removed_tests == 1


def test_full_overlap_with_skips_marks_partial_evidence():
    comparison = compare_revisions(
        revision("base", {"x": Outcome.PASSED}),
        revision("head", {"x": Outcome.SKIPPED}),
    )
    assert comparison.evidence.overlap_percent == 100
    assert comparison.evidence.quality == "partial"
    assert any("skipped" in warning for warning in comparison.evidence.warnings)


def test_unstable_history_is_partial_evidence():
    comparison = compare_revisions(
        revision("base", {"x": Outcome.PASSED}, {"x": Outcome.FAILED}),
        revision("head", {"x": Outcome.PASSED}, {"x": Outcome.PASSED}),
    )
    assert comparison.evidence.quality == "partial"
    assert len(comparison.flaky) == 1


@pytest.mark.parametrize("minimum,expected", [(0, 0), (50, 0), (51, 1), (100, 1)])
def test_minimum_overlap_enforcement(tmp_path, minimum, expected):
    base = _xml(tmp_path / "base.xml", "a", "b")
    head = _xml(tmp_path / "head.xml", "a", "c")
    report = tmp_path / f"report-{minimum}"
    assert main(["compare", "--base-xml", str(base), "--head-xml", str(head),
                 "--min-overlap", str(minimum), "--output", str(report)]) == expected
    payload = json.loads((report / "result.json").read_text(encoding="utf-8"))
    assert payload["evidence"]["overlap_percent"] == 50
    assert payload["schema_version"] == 1  # Additive schema, no breaking change.


@pytest.mark.parametrize("minimum", ["-1", "101", "nan", "inf"])
def test_minimum_overlap_rejects_invalid_threshold(tmp_path, minimum):
    base = _xml(tmp_path / "a.xml", "a")
    assert main(["compare", "--base-xml", str(base), "--head-xml", str(base),
                 "--min-overlap", minimum, "--output", str(tmp_path / "out")]) == 2


def test_no_fail_does_not_override_explicit_continuity_guard(tmp_path):
    base = _xml(tmp_path / "a.xml", "a")
    head = _xml(tmp_path / "b.xml", "b")
    assert main(["compare", "--base-xml", str(base), "--head-xml", str(head),
                 "--no-fail", "--min-overlap", "1",
                 "--output", str(tmp_path / "out")]) == 1


def test_github_output_exposes_quality_metadata(tmp_path, monkeypatch):
    base = _xml(tmp_path / "a.xml", "a", "b")
    head = _xml(tmp_path / "b.xml", "a")
    out = tmp_path / "GITHUB_OUTPUT"
    monkeypatch.setenv("GITHUB_OUTPUT", str(out))
    assert main(["compare", "--base-xml", str(base), "--head-xml", str(head),
                 "--github-output", "--output", str(tmp_path / "results")]) == 0
    content = out.read_text(encoding="utf-8")
    assert "shared_tests=1\n" in content
    assert "overlap_percent=50.00\n" in content
    assert "quality=partial\n" in content


def test_non_ascii_test_identity_is_preserved_in_json_and_html_escaped():
    comparison = compare_revisions(
        revision("base", {"a<b&": Outcome.PASSED}),
        revision("head", {"a<b&": Outcome.FAILED}),
    )
    html = to_html(comparison)
    assert "a&lt;b&amp;" in html
    assert "a<b&" not in html
    assert to_payload(comparison)["counts"]["regressions"] == 1

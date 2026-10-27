from regressionproof.compare import compare_revisions, summarize_test
from regressionproof.model import Outcome, RevisionResult, TestCase, TestRun


def revision(name, *runs):
    return RevisionResult(name, "f" * 40, tuple(TestRun({
        key: TestCase(key, Outcome(status)) for key, status in case_set.items()
    }, 0, 0.1) for case_set in runs))


def test_all_comparison_classes():
    baseline = revision("main", {
        "regression": "passed", "old_failure": "failed", "fixed": "error",
        "removed": "passed", "unchanged": "passed", "unstable": "passed",
        "skipped": "skipped",
    }, {
        "regression": "passed", "old_failure": "failed", "fixed": "error",
        "removed": "passed", "unchanged": "passed", "unstable": "failed",
        "skipped": "skipped",
    })
    head = revision("feature", {
        "regression": "failed", "old_failure": "failed", "fixed": "passed",
        "new_failure": "failed", "new_pass": "passed", "unchanged": "passed",
        "unstable": "passed", "skipped": "skipped",
    }, {
        "regression": "failed", "old_failure": "error", "fixed": "passed",
        "new_failure": "failed", "new_pass": "passed", "unchanged": "passed",
        "unstable": "passed", "skipped": "skipped",
    })
    comparison = compare_revisions(baseline, head)
    assert [item.key for item in comparison.regressions] == ["regression"]
    assert [item.key for item in comparison.new_failures] == ["new_failure"]
    # Assertion failure and test error are both stable failures for triage.
    assert [item.key for item in comparison.existing_failures] == ["old_failure"]
    assert [item.key for item in comparison.flaky] == ["unstable"]
    assert [item.key for item in comparison.fixed] == ["fixed"]
    assert [item.key for item in comparison.removed] == ["removed"]
    assert [item.key for item in comparison.added] == ["new_pass"]
    assert comparison.has_new_failure


def test_existing_failure_is_not_new():
    result = compare_revisions(revision("old", {"x": "failed"}),
                               revision("new", {"x": "error"}))
    assert len(result.existing_failures) == 1
    assert not result.has_new_failure


def test_incomplete_runs_are_not_regressions():
    result = compare_revisions(revision("base", {"x": "passed"}, {}),
                               revision("head", {"x": "failed"}, {"x": "failed"}))
    assert summarize_test(result.base, "x") == "incomplete"
    assert len(result.flaky) == 1
    assert not result.has_new_failure


def test_skipped_to_failure_is_not_certain_regression():
    result = compare_revisions(revision("base", {"x": "skipped"}),
                               revision("head", {"x": "failed"}))
    assert not result.has_new_failure
    assert len(result.other) == 1


def test_rejects_empty_run_groups():
    try:
        compare_revisions(RevisionResult("none", "", ()), revision("ok", {"x": "passed"}))
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")

"""Deterministic classification of observed test outcomes."""

from __future__ import annotations

from .model import ChangedTest, Comparison, Outcome, RevisionResult


_FAILURES = {Outcome.ERROR.value, Outcome.FAILED.value}


def summarize_test(revision: RevisionResult, key: str) -> str:
    observations = [run.tests[key].outcome.value if key in run.tests else "missing"
                    for run in revision.runs]
    if all(value == "missing" for value in observations):
        return "absent"
    if "missing" in observations:
        return "incomplete"
    unique = set(observations)
    if unique <= _FAILURES:
        return "failed"
    if len(unique) != 1:
        return "flaky"
    return observations[0]


def compare_revisions(base: RevisionResult, head: RevisionResult) -> Comparison:
    if not base.runs or not head.runs:
        raise ValueError("Both revisions must contain at least one run")
    keys = sorted({key for run in base.runs + head.runs for key in run.tests})
    groups: dict[str, list[ChangedTest]] = {
        group: [] for group in (
            "regressions", "new_failures", "existing_failures", "fixed", "flaky",
            "added", "removed", "other"
        )
    }
    for key in keys:
        before = summarize_test(base, key)
        after = summarize_test(head, key)
        item = ChangedTest(key, before, after)
        if "flaky" in {before, after} or "incomplete" in {before, after}:
            category = "flaky"
        elif before == "passed" and after in _FAILURES:
            category = "regressions"
        elif before == "absent" and after in _FAILURES:
            category = "new_failures"
        elif before in _FAILURES and after in _FAILURES:
            category = "existing_failures"
        elif before in _FAILURES and after == "passed":
            category = "fixed"
        elif before == "absent" and after != "absent":
            category = "added"
        elif after == "absent":
            category = "removed"
        else:
            category = "other"
        groups[category].append(item)
    return Comparison(base=base, head=head, **{key: tuple(value) for key, value in groups.items()})

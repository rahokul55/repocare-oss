"""Data contracts shared by parsing, comparison and reporting."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Outcome(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class TestCase:
    __test__ = False  # Avoid pytest treating this domain model as a test class.
    key: str
    outcome: Outcome
    detail: str = ""


@dataclass(frozen=True)
class TestRun:
    __test__ = False
    tests: dict[str, TestCase]
    exit_code: int
    elapsed_seconds: float


@dataclass(frozen=True)
class RevisionResult:
    ref: str
    sha: str
    runs: tuple[TestRun, ...]


@dataclass(frozen=True)
class ChangedTest:
    key: str
    base: str
    head: str


@dataclass(frozen=True)
class EvidenceSummary:
    """Test identity comparability, not coverage of executable source lines."""

    baseline_tests: int
    candidate_tests: int
    shared_tests: int
    added_tests: int
    removed_tests: int
    overlap_percent: float
    quality: str
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class Comparison:
    base: RevisionResult
    head: RevisionResult
    regressions: tuple[ChangedTest, ...]
    new_failures: tuple[ChangedTest, ...]
    existing_failures: tuple[ChangedTest, ...]
    fixed: tuple[ChangedTest, ...]
    flaky: tuple[ChangedTest, ...]
    added: tuple[ChangedTest, ...]
    removed: tuple[ChangedTest, ...]
    other: tuple[ChangedTest, ...]

    @property
    def evidence(self) -> EvidenceSummary:
        baseline = {key for run in self.base.runs for key in run.tests}
        candidate = {key for run in self.head.runs for key in run.tests}
        common = baseline & candidate
        overlap = round(100 * len(common) / len(baseline), 2) if baseline else 0.0
        warnings = []
        if not common:
            warnings.append("No shared test identities: results cannot establish continuity.")
        if baseline - candidate:
            warnings.append("Some baseline test identities are absent from the candidate.")
        if self.flaky:
            warnings.append("Unstable or incomplete observations limit comparison confidence.")
        if any(
            all(run.tests.get(key) is not None and
                run.tests[key].outcome == Outcome.SKIPPED for run in self.head.runs)
            for key in candidate
        ):
            warnings.append("Candidate has skipped tests; a skip is not a pass.")
        if not common:
            quality = "insufficient"
        elif warnings:
            quality = "partial"
        else:
            quality = "comparable"
        return EvidenceSummary(
            baseline_tests=len(baseline), candidate_tests=len(candidate),
            shared_tests=len(common), added_tests=len(candidate - baseline),
            removed_tests=len(baseline - candidate), overlap_percent=overlap,
            quality=quality, warnings=tuple(warnings),
        )

    @property
    def has_new_failure(self) -> bool:
        return bool(self.regressions or self.new_failures)

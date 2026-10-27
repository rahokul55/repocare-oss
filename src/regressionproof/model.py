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
    def has_new_failure(self) -> bool:
        return bool(self.regressions or self.new_failures)
